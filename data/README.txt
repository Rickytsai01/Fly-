Taiwan flight simulator map data

- taiwan-map.json: broad, downsampled elevation overview mesh and airport references.
- terrain20m/index.json + *.bin: streamable 20 m elevation tiles derived from the user-provided 2026 GeoTIFF.
- The browser loads nearby tiles around the aircraft and falls back to the overview mesh elsewhere.
- The 20 m source raster covers only its documented GeoTIFF bounds; it does not cover Magong Airport.
- No verified land-cover, road, river, or building data is included.
- The source is labeled DEM in the supplied index; this package does not independently certify bare-earth DTM vs surface DSM status.
