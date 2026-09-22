# Hop Plugins

A responsive Quarto website for spatial Apache Hop plugins.

## Local development

Requires Quarto (tested with 1.9.37).

```sh
quarto preview --port 4200
```

Build the static website with `quarto render`. Output is written to `_site/`.
No npm dependencies or external fonts are required. Quarto provides navigation
and client-side search. Docs, Plugins and Examples currently contain placeholder copy.

Edit `index.qmd` for the landing page, `styles.scss` for styling and `_quarto.yml`
for navigation and site settings. No custom domain is configured.

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
   select `main`, and click **Run workflow**.
4. The deployment's URL appears in the workflow run under the `github-pages`
   environment. Without a custom domain, it is
   <https://edigonzales.github.io/hop-plugins-site/>.

The selected branch is what gets rendered and deployed; it must be allowed by
any protection rules on the `github-pages` environment. Concurrent publications
are serialized so an in-progress deployment is not cancelled.
