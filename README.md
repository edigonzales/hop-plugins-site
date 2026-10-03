# Hop Plugins

A responsive Quarto website for spatial Apache Hop plugins.

## Local development

Requires Quarto (tested with 1.9.37).

```sh
quarto preview --port 4200
```

Build the static website with `quarto render`. Output is written to `_site/`.
No npm dependencies or external fonts are required. Quarto provides navigation
and client-side search. Getting Started, Plugins and Examples contain the installation guide, the bundled plugin catalog and six runnable vector tutorials.

Edit `index.qmd` for the landing page, `styles.scss` for styling and `_quarto.yml`
for navigation and site settings. Release metadata lives in `_variables.yml`; update the version, asset URLs and verification dates together. No custom domain is configured.

The hero illustration is stored in `assets/spatial-horse.png`. It was generated
with the built-in Imagegen tool; see `assets/illustration-prompt.md` for the prompt.

## Publish to GitHub Pages

The workflow `.github/workflows/publish-pages.yml` renders the site with Quarto
1.9.37 and deploys `_site/` using the official GitHub Pages artifact actions.
It runs **only on manual dispatch**, never automatically on pushes or pull requests.
No personal access token or `gh-pages` branch is needed.

1. Commit and push the workflow to the repository's default branch (`main`).
2. In **Settings → Pages → Build and deployment**, set **Source** to
   **GitHub Actions** (one-time setup).
3. Open **Actions → Publish website to GitHub Pages → Run workflow**,
   select `main`, optionally enter **distribution-version**, and click **Run workflow**.
   Enter an exact version without the leading `v`, or leave the field empty to use
   the latest published prerelease of `edigonzales/hop-distributions` (by publication
   date). Whitespace-only input also selects the latest prerelease. API errors or
   a missing prerelease fail the build; there is no fixed fallback version.
4. The deployment's URL appears in the workflow run under the `github-pages`
   environment. Without a custom domain, it is
   <https://edigonzales.github.io/hop-plugins-site/>.

The selected branch is what gets rendered and deployed; it must be allowed by
any protection rules on the `github-pages` environment. Concurrent publications
are serialized so an in-progress deployment is not cancelled.

The workflow logs the resolved distribution version and updates the version,
release link and ZIP download variables only in its build checkout before rendering.
It uses the Apache Hop version from `_variables.yml` and does not commit these
overrides or change verification dates and existing example evidence.

The feature cards use the unmodified `geo-alt-fill`, `database`, and `gear` SVGs
from [Bootstrap Icons v1.13.1](https://github.com/twbs/icons/tree/v1.13.1),
embedded in `index.qmd`. Their MIT license is in
[`assets/bootstrap-icons-LICENSE.txt`](assets/bootstrap-icons-LICENSE.txt).
The navigation and footer also use Bootstrap Icons through Quarto.
`assets/mark.svg` is the custom GeoHop logo.

## Example project and validation

`downloads/vector-formats/` contains ten pipelines, an isolated project configuration,
a local run configuration and three synthetic EPSG:2056 points (CC0). Pipelines use
`${PROJECT_HOME}`. Register the extracted folder as a Hop project before running them.
The Quarto pre-render hook packages the project as `downloads/vector-formats.zip`;
its explicit file list excludes generated datasets, logs and machine-specific audit files.

Run all examples with the documented distribution and an independent GDAL reader:

```sh
HOP_JAVA_HOME=/path/to/jdk-21 python3 scripts/verify-examples.py \
  --hop-home /path/to/hop --ogrinfo /path/to/ogrinfo
```

Use GDAL 3.13 or newer with native spatial Parquet support. A bundled GDAL may
require `GDAL_DATA` and `PROJ_DATA`. The check copies the project to a temporary
folder, runs ten pipelines, compares every feature's attributes and coordinates,
checks CRS and layer counts, and verifies that CREATE_FILE preserves an existing
GeoPackage when it fails. Logs and output stay in the reported temporary folder.

Real Hop screenshots are stored in `assets/examples/`. Recapture affected dialogs
and results when updating the distribution or changing the example settings.

Before publishing: run `quarto render`, then `python3 scripts/check-site.py`, and
inspect desktop/mobile layouts. The manual publishing workflow remains unchanged.


## Raster tutorials

The Examples hub groups projects by plugin and topic. The existing vector tutorial
URLs remain available; their shared setup now lives on `examples/vector-formats.qmd`.
The raster project includes eight independent pipelines, only building polygons,
and a lossless crop of the explicitly selected 2019 nDSM. Never substitute the
2023 raster when updating these tutorials.

`python3 scripts/package-examples.py` builds both downloadable projects from input
allowlists. Outputs and audit data must not be packaged. The normal site check also
checks raster bundle hashes, building-only selection and the ZonalStats source URLs.

Full raster verification (Python with GDAL >= 3.13, NumPy, Shapely; Java 21):

```sh
python3 scripts/verify-raster-examples.py --hop-home /path/to/hop --online
```

Set `HOP_JAVA_HOME`, `GDAL_DATA` and `PROJ_DATA` when required by the local installation.
Omit `--online` for offline verification. The verifier extracts the published ZIP
into a temporary project with a space in its path, runs all requested pipelines,
checks data independently, and leaves logs plus `results.json` in its reported folder.
Synthetic fixtures cover NoData, valid zero, polygon holes, outside zones and both
interpolation methods. Existing-output protection and network failure are checked.

The raster test record is fixed in `downloads/raster-processing/tested-environment.json`.
Do not update its test date or artifact hashes merely because a newer distribution
was selected by the publishing workflow. Recapture GUI screenshots after UI changes;
see `assets/examples/raster/README.md` for dimensions and provenance.
