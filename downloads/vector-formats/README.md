# GeoHop vector format examples

Extract the whole bundle before opening a pipeline. Keep data/, output/ and the .hpl files together. Create a Hop project named vector-formats with its Home folder set to this extracted folder and use the included project-config.json. Select the project, open a .hpl in Hop GUI and run with the included local run configuration. Paths use ${PROJECT_HOME}; no project-specific absolute path is needed.

Run shapefile.hpl, geopackage.hpl, filegdb.hpl, flatgeobuf.hpl, parquet.hpl and generate.hpl independently. Each reads data/sites.gpkg (3 XY points, EPSG:2056). Existing outputs are not overwritten.

After geopackage.hpl, optionally run geopackage-add-layer.hpl (creates sites_copy), then geopackage-append.hpl (sites increases to 6 features). Repeating the append adds another 3 rows.

After shapefile.hpl and filegdb.hpl, run read-shapefile.hpl and read-filegdb.hpl to read the generated datasets back into new GeoPackages. FlatGeobuf, Parquet and GENERATE are output-only in Vector Reader/Writer.

Before repeating a create example, delete only its generated output, or choose a new target. For a Shapefile delete all files with that stem; for FileGDB delete the entire generated .gdb directory. Never use the source path as the destination.

Instructions: https://edigonzales.github.io/hop-plugins-site/examples.html
