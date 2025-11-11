import geopandas as gpd
from sqlalchemy import create_engine

def main():
    print("Hello from python!")

    data_path = r"C:\Users\tek\Desktop\try\maplibre-tutorials\demo_data\RI_Wetlands.parquet"
    conn_str = "postgresql://postgres:admin@localhost:5432/geo"
    
    # Read your spatial data
    gdf = gpd.read_parquet(data_path)
    
    # save to shapefile for verification (optional)
    # gdf.to_file("../demo_data/RI_Wetlands.shp")

    # Create SQLAlchemy engine (✅ correct)
    engine = create_engine(conn_str)

    # Upload to PostGIS
    gdf.to_postgis("ri_wetlands", engine, if_exists="replace")

    print("Data uploaded successfully!")

if __name__ == "__main__":
    main()