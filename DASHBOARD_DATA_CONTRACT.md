# Dashboard data contract

Required daily file: `dashboard_data/LATEST_TOPN_WATCHLIST.csv`.

Core columns:
`date`, `code`, `watch_rank`, `signal_label`, `signal_score`, `selection_score`, `preferred_horizon_days`.

Recommended columns:
`selection_score_2d/3d/4d/5d`, `h5_hold25_rank_pct`,
`c1_pred_rank_excess_2d/3d/4d/5d`, `c1_pred_resid_2d/3d/4d/5d`,
`policy_pred_abs_return`, `adv20_hkd`, `market_cap_hkd`, `beta_market_60`,
and the `setup_*` diagnostics.

The app degrades gracefully when recommended fields are absent.
