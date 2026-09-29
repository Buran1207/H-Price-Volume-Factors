# V28-U Signal Engine R1.9 Research — 97D Global + Southbound + Static Sector

- R1.2/H5 anchor is preserved.
- R1.9 global control is fixed at 97 child features = R1.7 85 + PRICE_LOCATION_RAW; external promoted groups: ['SOUTHBOUND_FLOW'].
- Primary ranking head directly predicts future cross-sectional excess-return percentile.
- Fixed ranking policy: P4_RANK_2D5D.
- Fixed HK tradability profile: U4_10B_50M.
- Market action gate: NONE (G0_ALWAYS).
- R1.5 predicted-absolute-return threshold gate is retired.
- Top 20 is generated inside U4 every scored session; Top 1-5 is STRONG_BUY and the rest of Top-N is BUY. No market gate can zero the BUY list.
- Feature-family selection is TRAIN-only. The already-inspected DEV interval is evaluation only and never selects a group.

## Development validation
- H5/excess IC: 0.1131
- C1 residual IC: 0.0329
- Watchlist mean actual return: 0.054%
- Watchlist minus selected universe: 0.537%
- BUY active-day fraction: 100.0%
- BUY mean actual return on active days: 0.054%
- BUY minus selected universe on active days: 0.537%
- STRONG_BUY mean actual return on active days: 0.266%
- Mean watchlist turnover: 30.8%

June-August 2026 remains development validation, not pristine blind evidence. Southbound/sector conclusions must be selected from TRAIN only; DEV is evaluation only.
