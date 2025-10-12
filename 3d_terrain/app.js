const map = new maplibregl.Map({
  container: "map",
  zoom: 2,
  center: [0, 20],
  pitch: 0,
  bearing: 0,
  style: {
    version: 8,
    sources: {
      satellite: {
        type: "raster",
        tiles: [
          // "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg",
          //   `https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=${maptilerApiKey}`,
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        ],
        tileSize: 256,
        // attribution: "&copy; EOX Sentinel-2",
        // attribution: "&copy; MapTiler, &copy; OpenStreetMap contributors",
        attribution: "Esri, Maxar, Earthstar Geographics",
      },
      terrainSource: {
        type: "raster-dem",
        tiles: [
          "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
          //   `https://api.maptiler.com/tiles/terrain-terrarium/{z}/{x}/{y}.png?key=${maptilerApiKey}`,
          //   "https://api.mapbox.com/v4/mapbox.terrain-rgb/{z}/{x}/{y}.pngraw?access_token=pk.eyJ1Ijoic2psZGZoc2xkZjM0NCIsImEiOiJjbWdmNHFncHcwNGtkMmlxN2llOWJtMDA1In0.fK3BE5274_jxOfjFOgCaSA",
        ],
        encoding: "terrarium",
        tileSize: 256,
        maxzoom: 15,
        attribution: "AWS Terrain Tiles",
        // attribution: "&copy; MapTiler, &copy; OpenStreetMap contributors",
        // attribution: "Mapbox Terrain Tiles",
      },
    },
    layers: [
      {
        id: "satellite",
        type: "raster",
        source: "satellite",
      },
    ],
    terrain: {
      source: "terrainSource",
      exaggeration: 1.1,
    },
  },
});

// set map projection to globe
map.on("style.load", function () {
  map.setProjection({
    type: "globe",
  });
});

// add controls
map.addControl(new maplibregl.NavigationControl(), "top-right");
map.addControl(new maplibregl.ScaleControl(), "bottom-left");
map.addControl(new maplibregl.FullscreenControl(), "top-right");
map.addControl(
  new maplibregl.TerrainControl({
    source: "terrainSource",
    // exaggeration: 1,
  }),
  "top-right"
);
