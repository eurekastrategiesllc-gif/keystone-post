# Keystone Post

County news and campaign money for Pennsylvania candidates.

- `site-src/index.html` is the page. `site/` holds its data files.
- `build/fetch_feeds.py` pulls the outlets in `build/feeds.json`; `build/trend.py` rebuilds the News and Trending data; `build/check.py` decides whether the result is safe to publish.
- `.github/workflows/refresh.yml` runs those about every 30 minutes and publishes the site. If a check fails the live site is left as it is.
- The rolling story store lives on the `state` branch, which is overwritten on every run.
- The Consultants tab reads `site/cons/board.json` (firms paid by 2026 candidates and party committees, with their clients' results from `raw/pa_results_2026-11-26.json`). It is a snapshot built on Joe's Mac on 2026-11-26 and is not rebuilt here yet.
- Campaign money files (`site/area`, `site/camp`, and the money parts of `site/data.json`) are a snapshot and are not rebuilt here yet.

Federal law bars using individual contributor information from FEC reports to solicit contributions or for commercial purposes.
