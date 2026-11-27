# Keystone Post

County news and campaign money for Pennsylvania candidates.

- `site-src/index.html` is the page. `site/` holds its data files.
- `build/fetch_feeds.py` pulls the outlets in `build/feeds.json`; `build/trend.py` rebuilds the News and Trending data; `build/check.py` decides whether the result is safe to publish.
- `.github/workflows/refresh.yml` runs those about every 30 minutes and publishes the site. If a check fails the live site is left as it is.
- The rolling story store lives on the `state` branch, which is overwritten on every run.
- The Consultants tab reads `site/cons/board.json`: firms paid by 2026 candidates and party committees, with their clients' results. `build/cons.py` rebuilds it inside the money workflow, and `build/cons_check.py` keeps the old board if the new one looks wrong. `.github/workflows/results.yml` re-reads the state returns site every six hours (`build/results.py`); when results change it saves a new `raw/pa_results_<date>.json` and starts a money rebuild.
- Campaign money files (`site/area`, `site/camp`, and the money parts of `site/data.json`) are a snapshot and are not rebuilt here yet.

Federal law bars using individual contributor information from FEC reports to solicit contributions or for commercial purposes.
