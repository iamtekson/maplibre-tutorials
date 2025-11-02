import os
from fastapi import FastAPI, Response, HTTPException
import asyncpg
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# load environment variables from .env file
load_dotenv()

async def get_geometry_column(conn, table_name: str) -> str:
    """
    Detects the geometry column of a PostGIS table.
    Returns the column name (e.g., 'geom', 'geometry', etc.)
    Raises HTTPException if not found.
    """
    # Try geometry_columns (works for registered PostGIS tables)
    sql_geom = """
        SELECT f_geometry_column
        FROM public.geometry_columns
        WHERE f_table_schema = 'public' AND f_table_name = $1
        LIMIT 1;
    """
    row = await conn.fetchrow(sql_geom, table_name)
    if row:
        return row["f_geometry_column"]

    # Fallback: look for any geometry-typed column
    sql_info = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = $1
        AND udt_name IN ('geometry', 'geography')
        LIMIT 1;
    """
    row = await conn.fetchrow(sql_info, table_name)
    if row:
        return row["column_name"]

    raise HTTPException(status_code=400, detail=f"No geometry column found in {table_name}")


async def get_non_geom_columns(conn, table_name: str, geom_col: str) -> list[str]:
    """
    Returns a list of non-geometry columns for the given table.
    """
    sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = $1
        AND column_name <> $2
        ORDER BY ordinal_position;
    """
    rows = await conn.fetch(sql, table_name, geom_col)
    # Quote column names safely to preserve case and special characters
    return [f'"{r["column_name"]}"' for r in rows]

app = FastAPI(title="PostGIS Vector Tile Server")

# Enable CORS for all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL DSN from environment variable
PG_DSN = os.getenv("PG_DSN")

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(dsn=PG_DSN)

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()
    
@app.get("/{table_name}/vt/{z}/{x}/{y}.mvt")
async def get_vector_tile(table_name: str, z: int, x: int, y: int):
    if not table_name.isidentifier():
        raise HTTPException(status_code=400, detail="Invalid table name")

    extent = 4096
    tile_size = 256
    resolution = 156543.03392804097 / (2 ** z)
    origin_shift = 20037508.342789244

    minx = x * tile_size * resolution - origin_shift
    maxx = (x + 1) * tile_size * resolution - origin_shift
    miny = origin_shift - (y + 1) * tile_size * resolution
    maxy = origin_shift - y * tile_size * resolution

    async with app.state.pool.acquire() as conn:
        geom_col = await get_geometry_column(conn, table_name)
        non_geom_cols = await get_non_geom_columns(conn, table_name, geom_col)
        attr_cols = ", ".join([f"t.{c}" for c in non_geom_cols]) or ""

        sql = f"""
            WITH bounds AS (
                SELECT ST_MakeEnvelope({minx}, {miny}, {maxx}, {maxy}, 3857) AS geom
            ),
            mvtgeom AS (
                SELECT
                    ST_AsMVTGeom(
                        ST_Transform(t.{geom_col}, 3857),
                        bounds.geom,
                        {extent},
                        64,      -- buffer in pixels
                        false    -- do not clip geometry, prevents seams
                    ) AS geom
                    {',' if attr_cols else ''} {attr_cols}
                FROM "{table_name}" t, bounds
                WHERE ST_Intersects(ST_Transform(t.{geom_col}, 3857), bounds.geom)
            )
            SELECT ST_AsMVT(mvtgeom.*, '{table_name}', {extent}, 'geom') AS tile
            FROM mvtgeom;
        """


        row = await conn.fetchrow(sql)
        tile = row["tile"] if row and row["tile"] else None

    if not tile:
        return Response(status_code=204)

    return Response(content=tile, media_type="application/vnd.mapbox-vector-tile")


