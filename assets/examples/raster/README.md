# Raster tutorial visuals

Tested and captured 3 October 2026 from Apache Hop 2.19.0, Java 21.0.10 on macOS
ARM64, using the local installation specified for this task. Exact plugin JAR
hashes are recorded in downloads/raster-processing/tested-environment.json.

Hop ran in an isolated configuration and a copy of the downloadable project.
The main window was 1250 × 850 logical screen points, matching the earlier vector
series. Pipeline crops are 970 × 380 points (1940 × 760 pixels at Retina scale);
metrics crops are 970 × 350 points (1940 × 700 pixels). Transform dialogs are
captured at their actual window bounds, resized to show the relevant settings.
Screenshots are native macOS captures of real dialogs and completed runs.

The five dataset views (ndsm-result, bbox-result, polygon-result,
reproject-comparison, zonal-map) are Matplotlib plots of independently verified
Hop output files, not simulated UI screenshots. Recreate them with:

    python3 scripts/render-raster-results.py --project '/path/to/executed/raster processing'

This needs GDAL, NumPy and Matplotlib. A suitable executed project is left by
scripts/verify-raster-examples.py. No source-data images are fetched for these plots.
