from __future__ import annotations
import argparse, shutil
from pathlib import Path
import pandas as pd

def copy_if(src,dst):
    if src.exists():
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        print(f"synced: {src} -> {dst}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project-root",required=True)
    ap.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1]))
    a=ap.parse_args()
    project=Path(a.project_root).resolve()
    repo=Path(a.repo_root).resolve()
    data=repo/"dashboard_data"
    live=project/"live"/"v28_signal_r19_research_shadow"
    data.mkdir(parents=True,exist_ok=True)

    latest=live/"LATEST_TOPN_WATCHLIST.csv"
    copy_if(latest,data/"LATEST_TOPN_WATCHLIST.csv")
    copy_if(live/"LATEST_SIGNALS.csv",data/"LATEST_SIGNALS.csv")
    copy_if(live/"LATEST_BUY_TOPN.csv",data/"LATEST_BUY_TOPN.csv")

    # Full Top20 archive for future dates. Same-date reruns replace that date.
    full_hist=data/"TOP20_SNAPSHOT_HISTORY.csv.gz"
    if latest.exists():
        cur=pd.read_csv(latest,low_memory=False)
        if not cur.empty and "date" in cur:
            cur["date"]=pd.to_datetime(cur["date"],errors="coerce").dt.strftime("%Y-%m-%d")
            old=pd.read_csv(full_hist,low_memory=False) if full_hist.exists() else pd.DataFrame()
            if not old.empty and "date" in old:
                old["date"]=pd.to_datetime(old["date"],errors="coerce").dt.strftime("%Y-%m-%d")
                old=old[~old["date"].isin(set(cur["date"].dropna()))]
            cols=list(dict.fromkeys(list(old.columns)+list(cur.columns)))
            merged=pd.concat([old.reindex(columns=cols),cur.reindex(columns=cols)],ignore_index=True)
            sort=[c for c in ["date","watch_rank","rank"] if c in merged]
            if sort: merged=merged.sort_values(sort)
            merged.to_csv(full_hist,index=False,compression="gzip")
            print("archived full Top20 snapshot")

    hist=live/"SIGNAL_HISTORY.csv.gz"
    if hist.exists():
        h=pd.read_csv(hist,low_memory=False)
        cols=[c for c in ["date","code","watchlist_flag","watch_rank","signal_label","selection_score","signal_score","preferred_horizon_days"] if c in h]
        h[cols].tail(12000).to_csv(data/"SIGNAL_HISTORY_COMPACT.csv.gz",index=False,compression="gzip")
        print("synced compact history")
    print("Dashboard data sync complete.")

if __name__=="__main__":
    main()
