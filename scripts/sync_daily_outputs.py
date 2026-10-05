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

    hist=data/"SIGNAL_HISTORY_UNIFIED.csv.gz"
    if latest.exists():
        cur=pd.read_csv(latest,low_memory=False)
        if not cur.empty and "date" in cur:
            cur["date"]=pd.to_datetime(cur["date"],errors="coerce").dt.strftime("%Y-%m-%d")
            cur["evidence_class"]="LIVE SHADOW"
            old=pd.read_csv(hist,low_memory=False) if hist.exists() else pd.DataFrame()
            if not old.empty and "date" in old:
                old["date"]=pd.to_datetime(old["date"],errors="coerce").dt.strftime("%Y-%m-%d")
                dates=set(cur["date"].dropna())
                if "evidence_class" in old:
                    mask=old["date"].isin(dates) & old["evidence_class"].astype(str).eq("LIVE SHADOW")
                    old=old.loc[~mask]
            cols=list(dict.fromkeys(list(old.columns)+list(cur.columns)))
            merged=pd.concat([old.reindex(columns=cols),cur.reindex(columns=cols)],ignore_index=True)
            sort=[c for c in ["date","watch_rank"] if c in merged]
            if sort: merged=merged.sort_values(sort)
            merged.to_csv(hist,index=False,compression="gzip")
            print("updated SIGNAL_HISTORY_UNIFIED.csv.gz")
    print("Dashboard sync complete.")

if __name__=="__main__":
    main()
