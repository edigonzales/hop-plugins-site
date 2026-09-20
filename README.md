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
for navigation and site settings. No production domain or deployment is configured.

The hero illustration is stored in `assets/spatial-horse.png`. It was generated
with the built-in Imagegen tool; see `assets/illustration-prompt.md` for the prompt.
