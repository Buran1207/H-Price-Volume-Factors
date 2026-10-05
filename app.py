from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

APP_DIR = Path(__file__).resolve().parent
DATA = APP_DIR / "dashboard_data"
ASSETS = APP_DIR / "assets"

st.set_page_config(page_title="V28-U R1.9 | HK Quant Signal", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root {--navy:#102d50;--muted:#64748b;--line:#e7edf4;--soft:#f6f8fb;}
[data-testid="stAppViewContainer"]{background:#fff}
[data-testid="stSidebar"]{background:#f7f9fc;border-right:1px solid var(--line)}
.block-container{padding-top:1.35rem;padding-bottom:2rem;max-width:1550px}
h1,h2,h3{color:var(--navy);letter-spacing:-.02em}
div[data-testid="stMetric"]{background:#f8fafc;border:1px solid #e6ebf1;border-radius:10px;padding:14px 16px}
.small-note{font-size:.82rem;color:var(--muted)}
.kicker{font-size:.72rem;letter-spacing:.14em;font-weight:700;color:var(--muted);text-transform:uppercase}
.hero{padding:6px 0 12px;border-bottom:1px solid var(--line);margin-bottom:18px}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:8px;overflow:hidden}
.footnotes{margin-top:28px;padding:18px 20px;background:#f8fafc;border:1px solid #e6ebf1;border-radius:10px}
.footnotes h4{margin:0 0 10px;color:#102d50}
.footnotes p{font-size:.86rem;line-height:1.55;margin:.42rem 0;color:#475569}
.note-badge{font-weight:800;color:#294b70}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=120)
def load_csv(name):
    p=DATA/name
    return pd.read_csv(p,low_memory=False) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=120)
def load_json(name):
    p=DATA/name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def pct(x,digits=2):
    if x is None or pd.isna(x): return "—"
    return f"{float(x)*100:.{digits}f}%"
def num(x,digits=3):
    if x is None or pd.isna(x): return "—"
    return f"{float(x):.{digits}f}"
def hk_money(x):
    if x is None or pd.isna(x): return "—"
    x=float(x)
    if abs(x)>=1e9:return f"HK${x/1e9:.1f}bn"
    if abs(x)>=1e6:return f"HK${x/1e6:.0f}m"
    return f"HK${x:,.0f}"
def normalize_watch(df):
    if df.empty:return df
    d=df.copy()
    if "date" in d:d["date"]=pd.to_datetime(d["date"],errors="coerce")
    rank="watch_rank" if "watch_rank" in d else ("rank" if "rank" in d else None)
    if rank:d=d.sort_values(rank)
    return d
def notes(items):
    body="".join(f"<p><span class='note-badge'>{n}</span> {txt}</p>" for n,txt in items)
    st.markdown(f"<div class='footnotes'><h4>{'字段注释 / Field Notes' if ZH else 'Field Notes / 字段注释'}</h4>{body}</div>",unsafe_allow_html=True)

summary=load_json("V28_SIGNAL_R19_RESEARCH_SUMMARY.json")
watch=normalize_watch(load_csv("LATEST_TOPN_WATCHLIST.csv"))
snap=load_csv("11_DEV_VALIDATION_PER_SNAPSHOT.csv")
ablation=load_csv("04_TRAIN_FEATURE_GROUP_ABLATION_MULTI_HORIZON.csv")
state_diag=load_csv("06_H5_TOP_DECILE_STATE_DIAGNOSTICS.csv")
history=normalize_watch(load_csv("SIGNAL_HISTORY_UNIFIED.csv.gz"))

LANG=st.sidebar.selectbox("Language / 语言",["English","中文"],index=0)
ZH=LANG=="中文"
def tr(en,zh):return zh if ZH else en

PAGE_EN=["Daily Dashboard","Signal Explorer","Market & Validation","Model Architecture","Research Evidence"]
PAGE_ZH=["每日看板","个股信号","市场与验证","模型架构","研究证据"]
PAGE_MAP=dict(zip(PAGE_ZH,PAGE_EN))

with st.sidebar:
    if (ASSETS/"aam_logo.png").exists():st.image(str(ASSETS/"aam_logo.png"),width=180)
    st.markdown("### V28-U Signal Engine")
    st.caption(tr("R1.9 · Hong Kong Equities · Internal","R1.9 · 港股 · 内部使用"))
    page_label=st.radio(tr("Navigation","导航"),PAGE_ZH if ZH else PAGE_EN,label_visibility="collapsed")
    page=PAGE_MAP.get(page_label,page_label)
    st.divider()
    st.markdown(tr("**Production policy**","**生产规则**"))
    st.caption(tr("Top 20 inside U4 · Top 1–5 STRONG_BUY · 2D/3D/4D/5D = 40/30/20/10","U4 股票池内 Top20 · Top1–5 为 STRONG_BUY · 2D/3D/4D/5D = 40/30/20/10"))
    st.caption("H5 / Rank / Residual = 45 / 35 / 20")
    if st.button(tr("Refresh data","刷新数据"),use_container_width=True):
        st.cache_data.clear();st.rerun()

latest_label="—"
if not watch.empty and "date" in watch:
    dt=pd.to_datetime(watch["date"],errors="coerce").max()
    if pd.notna(dt):latest_label=dt.strftime("%Y-%m-%d")

st.markdown(f"""<div class="hero"><div class="kicker">{tr("AAM · QUANTITATIVE RESEARCH · HONG KONG EQUITIES","AAM · 量化研究 · 港股")}</div>
<h1 style="margin:.2rem 0 .25rem">{tr("V28-U R1.9 Signal Dashboard","V28-U R1.9 信号看板")}</h1>
<div class="small-note">{tr("Latest signal date","最新信号日期")}: <b>{latest_label}</b> · {tr("Cross-sectional 2–5 day ranking system","2–5 日横截面排序系统")} · {tr("Internal team use","团队内部使用")}</div></div>""",unsafe_allow_html=True)

# Historical snapshot selector shared by Daily Dashboard and Signal Explorer.
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
        evidence="LIVE SHADOW" if selected_date==latest_watch_date else None
        if evidence is None and not view_watch.empty and "evidence_class" in view_watch:
            _ev=view_watch["evidence_class"].dropna().astype(str).unique().tolist()
            evidence=_ev[0] if _ev else None
        if evidence=="TRAIN OOF":
            st.success(tr("Evidence Class: TRAIN OOF — expanding-window out-of-fold historical prediction.",
                          "证据类型：TRAIN OOF — 扩展窗口 Out-of-Fold 历史预测。"))
        elif evidence=="DEV VALIDATION":
            st.warning(tr("Evidence Class: DEV VALIDATION — development validation; not pristine blind OOS.",
                          "证据类型：DEV VALIDATION — 开发验证；不是 pristine blind OOS。"))
        elif evidence:
            st.info(tr("Evidence Class: LIVE SHADOW — archived daily production/shadow signal.",
                       "证据类型：LIVE SHADOW — 每日生产/Shadow 信号归档。"))
        if selected_date!=latest_watch_date:
            st.caption(tr("Only fields actually archived for this date are shown; unavailable historical fields are not reconstructed.",
                          "仅展示该日期实际归档字段；历史未保存字段不会推算或补造。"))

if page=="Daily Dashboard":
    if view_watch.empty:st.warning(tr("No latest watchlist found.","未找到最新观察名单。"));st.stop()
    topn=len(view_watch);strong=int((view_watch.get("signal_label",pd.Series(dtype=str))=="STRONG_BUY").sum())
    mean_score=view_watch["signal_score"].mean() if "signal_score" in view_watch else np.nan
    med_adv=view_watch["adv20_hkd"].median() if "adv20_hkd" in view_watch else np.nan
    c1,c2,c3,c4=st.columns(4)
    c1.metric(tr("Watchlist ①","观察名单 ①"),f"{topn} "+tr("names","只"))
    c2.metric("STRONG_BUY ②",f"{strong}")
    c3.metric(tr("Mean signal score ③","平均信号分 ③"),f"{mean_score:.1f}" if pd.notna(mean_score) else "—")
    c4.metric(tr("Median ADV20 ④","ADV20 中位数 ④"),hk_money(med_adv))

    st.subheader(tr("Ranked watchlist — "+(selected_date or latest_label),"排序观察名单 — "+(selected_date or latest_label)))
    rename={"watch_rank":tr("Rank ⑤","排名 ⑤"),"code":tr("Ticker ⑥","代码 ⑥"),"security_name":tr("Name ⑦","名称 ⑦"),
            "signal_label":tr("Signal ⑧","信号 ⑧"),"signal_score":tr("Signal Score ⑨","信号分 ⑨"),
            "selection_score":tr("Selection ⑩","选择分数 ⑩"),"preferred_horizon_days":tr("Preferred H ⑪","偏好期限 ⑪"),
            "adv20_hkd":"ADV20 ⑫","market_cap_hkd":tr("Market Cap ⑬","市值 ⑬")}
    keep=[c for c in rename if c in view_watch.columns]
    table=view_watch[keep].rename(columns=rename)
    if "ADV20 ⑫" in table:table["ADV20 ⑫"]=table["ADV20 ⑫"].map(hk_money)
    mc=tr("Market Cap ⑬","市值 ⑬")
    if mc in table:table[mc]=table[mc].map(hk_money)
    st.dataframe(table,use_container_width=True,hide_index=True,height=590)

    left,right=st.columns([1.15,1])
    with left:
        st.subheader(tr("Cross-horizon selection profile ⑭","跨期限选择分数 ⑭"))
        hcols=[f"selection_score_{h}d" for h in [2,3,4,5] if f"selection_score_{h}d" in view_watch]
        if hcols:
            chart=view_watch.head(10)[["code"]+hcols].melt("code",var_name="Horizon",value_name="Score")
            chart["Horizon"]=chart["Horizon"].str.extract(r"(\d+d)")[0]
            fig=px.line(chart,x="Horizon",y="Score",color="code",markers=True)
            fig.update_layout(height=390,legend_title_text="Ticker",margin=dict(l=10,r=10,t=20,b=10));st.plotly_chart(fig,use_container_width=True)
    with right:
        st.subheader(tr("Signal score distribution ⑮","信号分分布 ⑮"))
        if "signal_score" in view_watch:
            fig=px.bar(view_watch.sort_values("signal_score"),x="signal_score",y="code",orientation="h")
            fig.update_layout(height=390,showlegend=False,margin=dict(l=10,r=10,t=20,b=10));st.plotly_chart(fig,use_container_width=True)
    notes([
      ("①",tr("Number of securities in the displayed Top20 watchlist.","当前展示的 Top20 观察名单股票数量。")),
      ("②",tr("Count labeled STRONG_BUY; production rule is watch rank 1–5, not an independent probability classifier.","STRONG_BUY 数量；生产规则为观察名单排名 1–5，并非独立概率分类器。")),
      ("③",tr("Mean of SignalScore across the displayed watchlist. SignalScore = 100 × same-day cross-sectional percentile rank of FinalSelection.","观察名单 SignalScore 均值。SignalScore = 100 × FinalSelection 在当日股票横截面的百分位排名。")),
      ("④",tr("Median ADV20 of the watchlist; ADV20 = mean daily trading amount over the latest 20 trading days.","观察名单 ADV20 中位数；ADV20 = 最近20个交易日每日成交额的平均值。")),
      ("⑤",tr("WatchRank = descending rank of FinalSelection after the eligible-universe filter.","WatchRank = 可交易股票池过滤后按 FinalSelection 从高到低的名次。")),
      ("⑥",tr("Security code / ticker.","证券代码。")),("⑦",tr("Security name from the model output.","模型输出中的证券名称。")),
      ("⑧",tr("Signal label: ranks 1–5 = STRONG_BUY; ranks 6–20 = BUY.","信号标签：排名1–5=STRONG_BUY；6–20=BUY。")),
      ("⑨",tr("SignalScore = 100 × PctRank_CS(FinalSelection). It is not upside probability or predicted return.","SignalScore = 100 × PctRank_CS(FinalSelection)。不是上涨概率，也不是预测收益率。")),
      ("⑩",tr("FinalSelection = 0.40·S2D + 0.30·S3D + 0.20·S4D + 0.10·S5D, where Sh = 0.45·H5Rank + 0.35·RankPredRank_h + 0.20·ResidualPredRank_h.","FinalSelection = 0.40·S2D + 0.30·S3D + 0.20·S4D + 0.10·S5D；其中 Sh = 0.45·H5Rank + 0.35·RankPredRank_h + 0.20·ResidualPredRank_h。")),
      ("⑪",tr("Preferred horizon ∈ {2D,3D,4D,5D}. Exact selection rule is pending source-code audit; do not assume it equals argmax(Sh).","偏好期限 ∈ {2D,3D,4D,5D}。精确选择规则仍待源码审计，暂不能假定等于 argmax(Sh)。")),
      ("⑫",tr("ADV20 = 20-trading-day average trading amount; liquidity/capacity measure, not a prediction signal.","ADV20 = 过去20个交易日平均成交额；属于流动性/容量指标，不是预测信号。")),
      ("⑬",tr("Market-cap field from model data. Exact database share-count convention remains source-dependent.","模型数据中的市值字段；精确股本/市值数据库口径仍以数据源代码为准。")),
      ("⑭",tr("For h=2,3,4,5: Sh = 45% H5 rank + 35% Rank-head percentile + 20% Residual-head percentile.","对 h=2,3,4,5：Sh = 45% H5排名 + 35% Rank Head百分位 + 20% Residual Head百分位。")),
      ("⑮",tr("Distribution of SignalScore across the displayed watchlist.","当前观察名单中 SignalScore 的分布。"))
    ])

elif page=="Signal Explorer":
    if view_watch.empty:st.warning(tr("No latest watchlist available.","暂无最新观察名单。"));st.stop()
    ticker=st.selectbox(tr("Select security ①","选择股票 ①"),view_watch["code"].astype(str).tolist(),index=0)
    row=view_watch[view_watch["code"].astype(str).eq(ticker)].iloc[0];rank=row.get("watch_rank",row.get("rank",np.nan))
    a,b,c,d=st.columns(4)
    a.metric(tr("Watch rank ②","观察名单排名 ②"),f"#{int(rank)}" if pd.notna(rank) else "—")
    b.metric(tr("Signal score ③","信号分 ③"),f"{row.get('signal_score',np.nan):.1f}" if pd.notna(row.get("signal_score",np.nan)) else "—")
    c.metric(tr("Preferred horizon ④","偏好期限 ④"),f"{int(row.get('preferred_horizon_days'))}D" if pd.notna(row.get("preferred_horizon_days",np.nan)) else "—")
    d.metric(tr("Model label ⑤","模型标签 ⑤"),str(row.get("signal_label","—")))
    l,r=st.columns([1.15,1])
    with l:
        hs=[2,3,4,5];vals=[row.get(f"selection_score_{h}d",np.nan) for h in hs]
        fig=go.Figure(go.Bar(x=[f"{h}D" for h in hs],y=vals))
        fig.update_layout(title=tr("Selection score by horizon ⑥","各期限选择分数 ⑥"),height=350,yaxis_title="Score");st.plotly_chart(fig,use_container_width=True)
    with r:
        components=pd.DataFrame({"Component":["H5 rank ⑦","Rank head (2D) ⑧","Residual head (2D) ⑨"],
          "Value":[row.get("h5_hold25_rank_pct",np.nan),row.get("c1_pred_rank_excess_2d",np.nan),row.get("c1_pred_resid_2d",np.nan)]}).dropna()
        fig=px.bar(components,x="Value",y="Component",orientation="h",title=tr("Selected model diagnostics","模型诊断"))
        fig.update_layout(height=350);st.plotly_chart(fig,use_container_width=True)
    st.subheader(tr("Technical setup diagnostics ⑩","技术状态诊断 ⑩"))
    setup_map={"setup_trend_strength":tr("Trend strength","趋势强度"),"setup_extension_strength":tr("Extension","趋势延伸"),
      "setup_efficiency":tr("Efficiency","趋势效率"),"setup_breakout_strength":tr("Breakout","突破强度"),
      "setup_volume_confirmation":tr("Volume confirmation","成交确认"),"setup_acceleration":tr("Acceleration","加速度")}
    setup=pd.DataFrame({tr("Dimension","维度"):[v for k,v in setup_map.items() if k in view_watch],"Value":[row.get(k,np.nan) for k in setup_map if k in view_watch]}).dropna()
    if not setup.empty:
        fig=px.bar(setup,x=tr("Dimension","维度"),y="Value");fig.update_layout(height=330);st.plotly_chart(fig,use_container_width=True)
    notes([
      ("①",tr("Security selected from today's watchlist.","从当日观察名单选择的股票。")),
      ("②",tr("Descending rank of FinalSelection in the eligible universe.","FinalSelection 在可交易股票池中的降序名次。")),
      ("③",tr("100 × same-day cross-sectional percentile rank of FinalSelection; not probability.","100 × FinalSelection 当日横截面百分位；不是概率。")),
      ("④",tr("Preferred horizon in {2D,3D,4D,5D}; exact policy rule pending source audit.","偏好期限属于 {2D,3D,4D,5D}；精确 policy 规则待源码审计。")),
      ("⑤",tr("Rank-derived label: Top1–5 STRONG_BUY, Top6–20 BUY.","由排名派生的标签：Top1–5 STRONG_BUY，Top6–20 BUY。")),
      ("⑥",tr("Sh = 0.45·H5Rank + 0.35·RankPredRank_h + 0.20·ResidualPredRank_h.","Sh = 0.45·H5Rank + 0.35·RankPredRank_h + 0.20·ResidualPredRank_h。")),
      ("⑦",tr("Same-day cross-sectional percentile rank of the Frozen H5 anchor output.","Frozen H5 稳定锚输出的当日横截面百分位排名。")),
      ("⑧",tr("2D Rank-head prediction. The head learns future cross-sectional excess-return rank; the fusion uses its same-day percentile rank.","2D Rank Head 预测；目标为未来横截面超额收益排名，融合时使用其当日百分位排名。")),
      ("⑨",tr("2D Residual-head prediction. Residual target concept: R_stock − beta·R_market, isolating stock-specific return.","2D Residual Head 预测。Residual 目标概念：R_stock − beta·R_market，用于提取个股特异收益。")),
      ("⑩",tr("Trend Strength, Extension, Efficiency, Breakout, Volume Confirmation and Acceleration are scorer diagnostics. Their exact formulas are pending technical_state_features/source audit and are intentionally not invented here.","Trend Strength、Extension、Efficiency、Breakout、Volume Confirmation、Acceleration 为打分器诊断字段；精确公式待 technical_state_features/源码审计，此处不自行补公式。"))
    ])

elif page=="Market & Validation":
    dev=summary.get("dev_validation_metrics",{})
    st.subheader(tr("Development validation snapshot","开发验证快照"))
    a,b,c,d=st.columns(4)
    a.metric(tr("H5 / excess IC ①","H5 / 超额收益 IC ①"),num(dev.get("mean_h5_ic_excess"),4))
    b.metric(tr("Residual IC ②","Residual IC ②"),num(dev.get("mean_c1_ic_resid"),4))
    c.metric(tr("Watchlist mean return ③","观察名单平均收益 ③"),pct(dev.get("mean_watch_stock_return"),3))
    d.metric(tr("Watchlist – universe ④","观察名单 – 股票池 ④"),pct(dev.get("mean_watch_minus_universe_stock"),3))
    if not snap.empty and "date" in snap:
        s=snap.copy();s["date"]=pd.to_datetime(s["date"],errors="coerce")
        candidates=[c for c in ["watch_minus_universe_stock","watch_mean_stock_return","h5_ic_excess","c1_ic_resid"] if c in s]
        metric=st.selectbox(tr("Daily validation series ⑤","每日验证序列 ⑤"),candidates)
        fig=px.line(s,x="date",y=metric);fig.add_hline(y=0,line_width=1,line_dash="dot");fig.update_layout(height=420,xaxis_title="",yaxis_title="");st.plotly_chart(fig,use_container_width=True)
    notes([
      ("①",tr("Mean daily cross-sectional IC between H5 prediction and the excess-return target. Exact correlation convention (Pearson/Spearman) remains subject to training-code audit.","H5 预测与超额收益目标之间的日度横截面 IC 均值；Pearson/Spearman 的精确口径仍待训练源码审计。")),
      ("②",tr("Mean daily cross-sectional IC between Residual-head prediction and realized residual target.","Residual Head 预测与实际 Residual 目标之间的日度横截面 IC 均值。")),
      ("③",tr("Mean realized stock return of the daily watchlist. Exact horizon/policy alignment remains subject to result-generation code audit.","每日观察名单实际股票收益的均值；精确持有期/policy 对齐方式仍待结果生成源码审计。")),
      ("④",tr("Mean active spread: watchlist realized return minus eligible-universe realized return.","平均主动收益差：观察名单实际收益减去可选股票池实际收益。")),
      ("⑤",tr("Daily time series of the selected validation metric. June–August 2026 is development validation, not pristine blind OOS evidence.","所选验证指标的日度时间序列。2026年6–8月属于开发验证，并非 pristine blind OOS 证据。"))
    ])

elif page=="Model Architecture":
    st.subheader(tr("How R1.9 produces the daily ranking","R1.9 如何生成每日排序"))
    st.markdown(tr(
"""**Market state ①** — 56 market-regime variables shared across stocks on the same date.

**Stock state ②** — 41 stock technical-state variables. 97D Core = 56 Market + 41 Stock.

**Child models ③** — Rank / Residual × 2D / 3D / 4D / 5D = 8 child models.

**Single-horizon fusion ④** — Sh = 45% H5 + 35% Rank + 20% Residual, after same-day percentile conversion.

**Multi-horizon fusion ⑤** — FinalSelection = 40% S2D + 30% S3D + 20% S4D + 10% S5D.

**Tradability & output ⑥** — U4 filter → daily ranking → Top20; ranks 1–5 = STRONG_BUY.""",
"""**市场状态 ①** — 56 个 Market Regime 变量；同一天在所有股票间共享。

**个股状态 ②** — 41 个个股技术状态变量。97D Core = 56 Market + 41 Stock。

**Child Models ③** — Rank / Residual × 2D / 3D / 4D / 5D = 8 个子模型。

**单期限融合 ④** — 各输出先转当日横截面百分位，再计算 Sh = 45% H5 + 35% Rank + 20% Residual。

**跨期限融合 ⑤** — FinalSelection = 40% S2D + 30% S3D + 20% S4D + 10% S5D。

**可交易性与输出 ⑥** — U4 过滤 → 每日排序 → Top20；排名1–5 = STRONG_BUY。"""))
    c1,c2,c3=st.columns(3)
    c1.info(tr("**Frozen H5 ⑦**\n\n78-dimensional stable anchor","**Frozen H5 ⑦**\n\n78维稳定锚"))
    c2.info(tr("**97D Core ⑧**\n\n56 market + 41 stock","**97D Core ⑧**\n\n56市场 + 41个股"))
    c3.info(tr("**Current explainability input ⑨**\n\n106 = 97D Core + 9 Southbound","**当前 Explainability 输入 ⑨**\n\n106 = 97D Core + 9 Southbound"))
    weights=pd.DataFrame({"Layer":["H5","Rank","Residual","2D","3D","4D","5D"],"Weight":[45,35,20,40,30,20,10],"Group":["Single-horizon"]*3+["Multi-horizon"]*4})
    fig=px.bar(weights,x="Weight",y="Layer",orientation="h",facet_col="Group",text="Weight");fig.update_layout(height=360,showlegend=False);st.plotly_chart(fig,use_container_width=True)
    notes([
      ("①",tr("Z_t=(z1,…,z56): market-state vector shared by all stocks on date t.","Z_t=(z1,…,z56)：日期t所有股票共享的市场状态向量。")),
      ("②",tr("X_i,t=(x1,…,x41): stock-specific technical-state vector.","X_i,t=(x1,…,x41)：股票i在日期t的个股技术状态向量。")),
      ("③",tr("8 child models = 2 targets × 4 horizons: Rank/Residual × 2D/3D/4D/5D.","8个 Child Models = 2类目标 × 4个期限：Rank/Residual × 2D/3D/4D/5D。")),
      ("④",tr("Sh = .45 H5Rank + .35 RankPredRank_h + .20 ResidualPredRank_h.","Sh = .45 H5Rank + .35 RankPredRank_h + .20 ResidualPredRank_h。")),
      ("⑤",tr("FinalSelection = .40 S2D + .30 S3D + .20 S4D + .10 S5D.","FinalSelection = .40 S2D + .30 S3D + .20 S4D + .10 S5D。")),
      ("⑥",tr("U4 is the tradability layer covering market cap, liquidity, trading continuity, price and turnover stability before final Top20 output.","U4 是最终 Top20 前的可交易性层，覆盖市值、流动性、交易连续性、股价和成交稳定性。")),
      ("⑦",tr("Frozen 78-dimensional H5 model used as the stable anchor; 45% weight inside each horizon fusion.","冻结的78维 H5 稳定锚模型；在每个期限融合中权重45%。")),
      ("⑧",tr("97D Core = 56 Market Regime + 41 Stock Technical.","97D Core = 56 Market Regime + 41 Stock Technical。")),
      ("⑨",tr("The 2026-09-29 explainability study reports production input as 106 = 97D Core + 9 Southbound. This note distinguishes current explainability input from the 97D core definition.","2026-09-29 Explainability Study 报告生产输入为106 = 97D Core + 9 Southbound；此处明确区分当前解释性输入与97D Core定义。"))
    ])

elif page=="Research Evidence":
    st.subheader(tr("TRAIN-only feature-family evidence","仅 TRAIN 样本的因子族证据"))
    if not ablation.empty:
        rename={"variant":tr("variant ①","variant ①"),"feature_count":tr("feature_count ②","feature_count ②"),
          "mean_selection_ic_p4":tr("mean_selection_ic_p4 ③","mean_selection_ic_p4 ③"),
          "mean_precision_at_20":tr("mean_precision_at_20 ④","mean_precision_at_20 ④"),
          "mean_top20_minus_universe_p4":tr("mean_top20_minus_universe_p4 ⑤","mean_top20_minus_universe_p4 ⑤"),
          "family":tr("family ⑥","family ⑥")}
        cols=[c for c in rename if c in ablation]
        st.dataframe(ablation[cols].rename(columns=rename),use_container_width=True,hide_index=True)
        if "mean_selection_ic_p4" in ablation:
            fig=px.bar(ablation,x="mean_selection_ic_p4",y="variant",orientation="h");fig.update_layout(height=330);st.plotly_chart(fig,use_container_width=True)
    if not state_diag.empty:
        st.subheader(tr("H5 top-decile state diagnostics","H5 前十分位状态诊断"))
        split=st.selectbox(tr("Evidence split ⑦","证据样本 ⑦"),state_diag["split"].dropna().unique().tolist())
        d=state_diag[state_diag["split"].eq(split)]
        dim=st.selectbox(tr("Dimension ⑧","维度 ⑧"),d["dimension"].dropna().unique().tolist());d=d[d["dimension"].eq(dim)]
        value=st.selectbox(tr("Residual horizon ⑨","Residual 期限 ⑨"),[c for c in ["mean_resid_2d","mean_resid_3d","mean_resid_5d"] if c in d])
        fig=px.bar(d,x="bucket",y=value);fig.update_layout(height=350,xaxis_title="",yaxis_title=value);st.plotly_chart(fig,use_container_width=True)
    notes([
      ("①",tr("Research variant / feature-family experiment identifier.","研究 variant / 因子族实验标识。")),
      ("②",tr("Number of input features used by that experiment: K = #Features.","该实验使用的输入特征数量：K = #Features。")),
      ("③",tr("Mean cross-sectional selection IC under policy P4. Exact target/correlation convention remains subject to training-code audit.","P4 policy 下的平均横截面 Selection IC；精确 target/相关系数口径仍待训练源码审计。")),
      ("④",tr("Precision@20 = number of Top20 predictions that actually fall in the defined target-strong group ÷ 20.","Precision@20 = Top20 预测中实际进入目标强势组的股票数 ÷ 20。")),
      ("⑤",tr("Mean realized-return spread: Top20 minus eligible universe under P4.","P4 下 Top20 实际收益减可选股票池实际收益的平均差。")),
      ("⑥",tr("Feature family associated with the research variant.","该研究 variant 对应的特征家族。")),
      ("⑦",tr("Evidence sample/split used for the state diagnostic.","状态诊断所使用的证据样本/数据切分。")),
      ("⑧",tr("State variable/dimension used to bucket H5 top-decile observations.","对 H5 前十分位样本进行分桶的状态变量/维度。")),
      ("⑨",tr("Mean residual outcome at the selected 2D/3D/5D horizon conditional on the state bucket. Exact realized-target construction remains source-code-defined.","在所选状态 bucket 条件下的2D/3D/5D平均 Residual 结果；实际 target 的精确构造仍以源码为准。"))
    ])

st.divider()
st.caption(tr("V28-U Signal Engine R1.9 · Internal quantitative research dashboard · Circled numbers map fields to definitions at the bottom of each page.","V28-U Signal Engine R1.9 · 内部量化研究看板 · 字段后的圈数字对应每页底部的数学定义与注释。"))
