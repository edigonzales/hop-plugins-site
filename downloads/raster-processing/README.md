# Raster processing in Spatial Hop

Extract the whole ZIP into a writable folder. In Hop GUI create the project
`raster-processing`, select this folder as its Home folder and use the included
`project-config.json`. Select the included `local` pipeline run configuration.
Open any of the eight `.hpl` files. Pipelines are independent; only `zonal-online.hpl`
requires internet. Keep `data/` unchanged and the `output/` directory present.

Use new output filenames or remove only the previously generated outputs before
repeating a pipeline. Overwrite is disabled. No additional GDAL installation is
needed to run these examples. Maintainer verification uses GDAL independently.

The `data/buildings.gpkg` file contains only the 33 buildings selected with
`art_txt = 'Gebaeude'` from source 2549. `building_id` is a copy of the original
GeoPackage primary key `T_Id`, exposed as a regular attribute so it survives
pipeline processing. Original attributes and the INTERLIS identifier remain.
The raster is an unchanged-grid crop of the explicitly selected 2019 building
nDSM, not the 2023 dataset. See `data/README.md` for provenance and data terms.

Tested on 3 October 2026 with Apache Hop 2.19.0, Java 21.0.10 and the local spatial
plugin builds identified by SHA-256 in `tested-environment.json`. This fixed test
record is independent of the website's latest distribution download link.

Tutorials: https://hop.interlis.guru/examples/raster-processing.html

`expected-statistics.json` contains independently verified statistics for all 33 buildings.
