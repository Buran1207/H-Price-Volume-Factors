# V28-U R1.9 Streamlit Team Dashboard

Professional internal dashboard for the V28-U R1.9 Hong Kong equity short-cycle cross-sectional ranking model.

## What the dashboard shows

- **Daily Dashboard**: latest Top-20 watchlist, STRONG_BUY count, signal score, ADV20 and 2D–5D score profile.
- **Signal Explorer**: one-name drill-down across horizon scores, H5 / Rank / Residual diagnostics and technical setup diagnostics.
- **Market & Validation**: development-validation IC, watchlist return and daily validation series.
- **Model Architecture**: stable description of the production ranking logic.
- **Research Evidence**: TRAIN-only feature-family evidence and state diagnostics.

The dashboard deliberately does **not** expose the model's problem/optimization discussion. It is designed around stable model logic and output fields so later R1.x updates can be accommodated by changing the data files rather than rebuilding the UI.

## Model logic represented in the UI

R1.9 is a 2–5 trading-day Hong Kong equity cross-sectional ranking system. Within each horizon, the score blends H5 / Rank / Residual at 45% / 35% / 20%. Across horizons, 2D / 3D / 4D / 5D weights are 40% / 30% / 20% / 10%. U4 tradability filtering is applied before the final daily ranking. Top 20 is the watchlist and Top 1–5 is STRONG_BUY.

## Run locally

```bash
py -3.12 -m pip install -r requirements.txt
py -3.12 -m streamlit run app.py
```

## Daily after-close workflow

Your existing R1.9 scoring script writes:
- `live/v28_signal_r19_research_shadow/LATEST_TOPN_WATCHLIST.csv`
- `live/v28_signal_r19_research_shadow/LATEST_SIGNALS.csv`
- `live/v28_signal_r19_research_shadow/LATEST_BUY_TOPN.csv`
- `live/v28_signal_r19_research_shadow/SIGNAL_HISTORY.csv.gz`

After the model has finished its normal daily scoring, run:

```bat
UPDATE_DASHBOARD_AFTER_CLOSE.bat "C:\YOUR_V28_PROJECT_ROOT"
```

That script:
1. copies only dashboard-safe output fields/files into `dashboard_data/`;
2. creates a compact signal history;
3. commits the changed dashboard data;
4. pushes to `origin main`.

If your Streamlit deployment watches GitHub `main`, the site will redeploy from the new data automatically.

## First push to GitHub main

From this folder:

```bash
git init
git branch -M main
git add .
git commit -m "V28 R1.9 Streamlit dashboard"
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Then deploy `app.py` on Streamlit Community Cloud or your internal Streamlit host.

## Data/security design

The repository intentionally excludes the trained `.joblib` model and the 100MB+ raw full-universe prediction file. The team-facing site needs model **outputs**, not model weights. If the repository is private, keep it private and restrict Streamlit access according to your firm's policy.

## Updating for future model versions

The UI is tolerant of missing optional columns. Keep the stable daily output names where possible. If R1.10/R2.0 adds fields, add them to `scripts/sync_daily_outputs.py` and the relevant dashboard page without changing the daily operating workflow.


## Bilingual UI

A language selector (`Language / 语言`) is available in the sidebar. Users can switch the dashboard between English and Simplified Chinese without changing any data files.
