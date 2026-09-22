# Synthetic sites

Three invented point features in EPSG:2056 (CH1903+ / LV95), created for the GeoHop tutorials. These are not surveyed locations.

| site_id | name | height_m | X | Y |
|---|---|---|---|---|
| 1 | Aare | 430.50 | 2600000 | 1200000 |
| 2 | Brücke | 432.25 | 2600100 | 1200050 |
| 3 | Park | 428.75 | 2600200 | 1200100 |

`sites.gpkg` is the canonical input; layer `sites`. `sites.csv` lists the source coordinates and attributes for independent comparison. `height_m` is an attribute, not a Z coordinate.

Original tutorial data: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/). Pipelines: MIT (see LICENSE.txt in the bundle).
