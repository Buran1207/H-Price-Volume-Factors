
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
import pandas as pd

def copy_if(src: Path, dst: Path):
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"synced: {src} -> {dst}")

def main():
    ap=argparse.ArgumentParser(description="Sync V28 R1.9 daily outputs into the Streamlit repository.")
    ap.add_argument("--project-root", required=True, help="Root of the installed V28 project.")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args=ap.parse_args()
    project=Path(args.project_root).resolve()
    repo=Path(args.repo_root).resolve()
    data=repo/"dashboard_data"
    live=project/"live"/"v28_signal_r19_research_shadow"

    copy_if(live/"LATEST_TOPN_WATCHLIST.csv", data/"LATEST_TOPN_WATCHLIST.csv")
    copy_if(live/"LATEST_SIGNALS.csv", data/"LATEST_SIGNALS.csv")
    copy_if(live/"LATEST_BUY_TOPN.csv", data/"LATEST_BUY_TOPN.csv")

    hist=live/"SIGNAL_HISTORY.csv.gz"
    if hist.exists():
        h=pd.read_csv(hist, low_memory=False)
        cols=[c for c in ["date","code","watchlist_flag","watch_rank","signal_label","selection_score","signal_score","preferred_horizon_days"] if c in h]
        h[cols].tail(12000).to_csv(data/"SIGNAL_HISTORY_COMPACT.csv.gz",index=False,compression="gzip")
        print("synced compact history")
    print("Dashboard data sync complete.")

if __name__=="__main__":
    main()
