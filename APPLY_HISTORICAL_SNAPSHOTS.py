from pathlib import Path

p=Path("app.py")
if not p.exists():
    raise SystemExit("Run this script from the repository root beside app.py.")
s=p.read_text(encoding="utf-8")

needle='state_diag=load_csv("06_H5_TOP_DECILE_STATE_DIAGNOSTICS.csv")\n'
if 'history=normalize_watch' not in s:
    s=s.replace(needle, needle+'history=normalize_watch(load_csv("SIGNAL_HISTORY_COMPACT.csv.gz"))\n')

marker='if page=="Daily Dashboard":\n'
selector="""# Historical snapshot selector shared by Daily Dashboard and Signal Explorer.
view_watch=watch.copy()
selected_date=None
if page in ["Daily Dashboard","Signal Explorer"]:
    _dates=[]
    for _df in [history,watch]:
        if not _df.empty and "date" in _df:
            _dates += pd.to_datetime(_df["date"],errors="coerce").dropna().dt.strftime("%Y-%m-%d").tolist()
    available_dates=sorted(set(_dates),reverse=True)
    if available_dates:
        selected_date=st.selectbox(
            tr("Signal Date / Historical Snapshot","信号日期 / 历史快照"),
            available_dates,index=0,
            help=tr("Choose a historical signal date; latest remains default.","选择历史信号日期；默认仍为最新信号日。"))
        latest_watch_date=None
        if not watch.empty and "date" in watch:
            _mx=pd.to_datetime(watch["date"],errors="coerce").max()
            if pd.notna(_mx): latest_watch_date=_mx.strftime("%Y-%m-%d")
        if selected_date==latest_watch_date:
            view_watch=watch.copy()
        elif not history.empty and "date" in history:
            _hd=pd.to_datetime(history["date"],errors="coerce").dt.strftime("%Y-%m-%d")
            view_watch=normalize_watch(history.loc[_hd.eq(selected_date)].copy())
        if selected_date!=latest_watch_date:
            st.info(tr("Historical Snapshot: only fields actually archived for that date are shown; missing fields are not reconstructed.",
                       "历史快照：仅展示该日期实际归档的字段；未保存字段不会推算或补造。"))

"""
if 'Historical snapshot selector shared' not in s:
    s=s.replace(marker,selector+marker,1)

start=s.index('if page=="Daily Dashboard":')
end=s.index('elif page=="Signal Explorer":')
b=s[start:end]
for a,c in [
('watch.empty','view_watch.empty'),('len(watch)','len(view_watch)'),
('watch.get(','view_watch.get('),('watch["signal_score"]','view_watch["signal_score"]'),
('"signal_score" in watch','"signal_score" in view_watch'),
('watch["adv20_hkd"]','view_watch["adv20_hkd"]'),('"adv20_hkd" in watch','"adv20_hkd" in view_watch'),
('if c in watch.columns','if c in view_watch.columns'),('table=watch[keep]','table=view_watch[keep]'),
('if f"selection_score_{h}d" in watch','if f"selection_score_{h}d" in view_watch'),
('watch.head(10)','view_watch.head(10)'),('watch.sort_values("signal_score")','view_watch.sort_values("signal_score")')]:
    b=b.replace(a,c)
b=b.replace('tr("Today\'s ranked watchlist","今日排序观察名单")',
            'tr("Ranked watchlist — "+(selected_date or latest_label),"排序观察名单 — "+(selected_date or latest_label))')
s=s[:start]+b+s[end:]

start=s.index('elif page=="Signal Explorer":')
end=s.index('elif page=="Market & Validation":')
b=s[start:end]
for a,c in [('watch.empty','view_watch.empty'),('watch["code"]','view_watch["code"]'),('row=watch[','row=view_watch['),('if k in watch','if k in view_watch')]:
    b=b.replace(a,c)
s=s[:start]+b+s[end:]

p.write_text(s,encoding="utf-8")
print("Historical selector patch applied to app.py.")
