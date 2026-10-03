# Data provenance and terms

Source: Canton of Solothurn, Amt für Geoinformation. Retrieved 3 October 2026.

- Buildings: [Amtliche Vermessung, MOpublic, dataset 2549](https://files.geo.so.ch/ch.so.agi.av.mopublic/aktuell/2549.ch.so.agi.av.mopublic.gpkg.zip).
  Select only `art_txt = 'Gebaeude'` from `bodenbedeckung`: 33 polygons in EPSG:2056.
  The GeoPackage contains a single layer, `buildings`. Original feature IDs are
  preserved as the primary key `T_Id` and copied to the ordinary field `building_id`.
  No other land-cover categories are included.
- Raster: [Gebäude digitales Oberflächenmodell (2019)](https://data.geo.so.ch/?filter=ch.so.agi.lidar_2019.ndsm_buildings),
  [original GeoTIFF](https://files.geo.so.ch/ch.so.agi.lidar_2019.ndsm_buildings/aktuell/ch.so.agi.lidar_2019.ndsm_buildings.tif).
  `ndsm-2019.tif` is a losslessly compressed crop around the buildings, with a
  10-metre margin rounded outwards to source pixel boundaries. No resampling,
  reprojection or alteration of pixel values was applied. EPSG:2056, 0.25-metre
  pixels, Float32, NoData -9999, one band. Heights are in metres above terrain.

The building inventory is newer than the LiDAR acquisition. Missing valid nDSM
pixels under a building produce `NO_VALID_PIXELS`, not an assumed height of zero.
Statistics describe raster samples inside the footprint, not an exact surveyed
building height or roof maximum.

[Source data terms](https://files.geo.so.ch/nutzungsbedingungen.html): free use for
commercial and non-commercial purposes; attribution is recommended. The MIT
license for tutorial code does not replace these source-data terms. Credit:
© Kanton Solothurn, Amt für Geoinformation, MOpublic and LiDAR 2019.

`provenance.json` records source URLs, source-window coordinates, metadata and
SHA-256 checksums. It also records the checksum of the downloaded source ZIP.
