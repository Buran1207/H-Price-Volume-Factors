
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
:root { --navy:#102d50; --ink:#142033; --muted:#64748b; --line:#e7edf4; --soft:#f6f8fb; --red:#e21b23; }
[data-testid="stAppViewContainer"] {background:#ffffff;}
[data-testid="stSidebar"] {background:#f7f9fc; border-right:1px solid #e7edf4;}
.block-container {padding-top:1.35rem; padding-bottom:2rem; max-width:1550px;}
h1,h2,h3 {color:#102d50; letter-spacing:-0.02em;}
div[data-testid="stMetric"] {background:#f8fafc; border:1px solid #e6ebf1; border-radius:10px; padding:14px 16px;}
.small-note {font-size:0.82rem;color:#64748b;}
.kicker {font-size:.72rem;letter-spacing:.14em;font-weight:700;color:#64748b;text-transform:uppercase;}
.hero {padding:6px 0 12px 0;border-bottom:1px solid #e7edf4;margin-bottom:18px;}
.tag {display:inline-block;padding:3px 8px;border-radius:999px;background:#eef3f8;color:#294b70;font-size:.75rem;font-weight:600;margin-right:5px;}
.buy {color:#0f7a4f;font-weight:700}.strong {color:#b42318;font-weight:800}
[data-testid="stDataFrame"] {border:1px solid #e7edf4;border-radius:8px;overflow:hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=120)
def load_csv(name):
    p = DATA / name
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=120)
def load_json(name):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def pct(x, digits=2):
    if x is None or pd.isna(x): return "—"
    return f"{float(x)*100:.{digits}f}%"

def num(x, digits=3):
    if x is None or pd.isna(x): return "—"
    return f"{float(x):.{digits}f}"

def hk_money(x):
    if x is None or pd.isna(x): return "—"
    x=float(x)
    if abs(x)>=1e9: return f"HK${x/1e9:.1f}bn"
    if abs(x)>=1e6: return f"HK${x/1e6:.0f}m"
    return f"HK${x:,.0f}"

def normalize_watch(df):
    if df.empty: return df
    d=df.copy()
    if "date" in d: d["date"]=pd.to_datetime(d["date"], errors="coerce")
    rank = "watch_rank" if "watch_rank" in d else ("rank" if "rank" in d else None)
    if rank: d=d.sort_values(rank)
    return d

summary=load_json("V28_SIGNAL_R19_RESEARCH_SUMMARY.json")
watch=normalize_watch(load_csv("LATEST_TOPN_WATCHLIST.csv"))
snap=load_csv("11_DEV_VALIDATION_PER_SNAPSHOT.csv")
ablation=load_csv("04_TRAIN_FEATURE_GROUP_ABLATION_MULTI_HORIZON.csv")
state_diag=load_csv("06_H5_TOP_DECILE_STATE_DIAGNOSTICS.csv")
curves=load_csv("07_CONDITIONAL_EXPECTATION_CURVES_2D_5D.csv")
history=load_csv("SIGNAL_HISTORY_COMPACT.csv.gz")

LANG = st.sidebar.selectbox("Language / 语言", ["English", "中文"], index=0)
ZH = LANG == "中文"

def tr(en, zh):
    return zh if ZH else en

PAGE_EN = ["Daily Dashboard","Signal Explorer","Market & Validation","Model Architecture","Research Evidence"]
PAGE_ZH = ["每日看板","个股信号","市场与验证","模型架构","研究证据"]
PAGE_MAP = dict(zip(PAGE_ZH, PAGE_EN))


with st.sidebar:
    if (ASSETS/"aam_logo.png").exists():
        st.image(str(ASSETS/"aam_logo.png"), width=180)
    st.markdown("### V28-U Signal Engine")
    st.caption(tr("R1.9 · Hong Kong Equities · Internal", "R1.9 · 港股 · 内部使用"))
    page_label = st.radio(
        tr("Navigation", "导航"),
        PAGE_ZH if ZH else PAGE_EN,
        label_visibility="collapsed",
    )
    page = PAGE_MAP.get(page_label, page_label)
    st.divider()
    st.markdown(tr("**Production policy**", "**生产规则**"))
    st.caption(tr("Top 20 inside U4 · Top 1–5 STRONG_BUY · 2D/3D/4D/5D = 40/30/20/10",
                  "U4 股票池内 Top20 · Top1–5 为 STRONG_BUY · 2D/3D/4D/5D = 40/30/20/10"))
    st.caption(tr("H5 / Rank / Residual = 45 / 35 / 20",
                  "H5 / Rank / Residual = 45 / 35 / 20"))
    if st.button(tr("Refresh data", "刷新数据"), use_container_width=True):
        st.cache_data.clear()
        st.rerun()

latest_label="—"
if not watch.empty and "date" in watch:
    dt=pd.to_datetime(watch["date"],errors="coerce").max()
    if pd.notna(dt): latest_label=dt.strftime("%Y-%m-%d")

st.markdown(
    f"""<div class="hero"><div class="kicker">{tr("AAM · QUANTITATIVE RESEARCH · HONG KONG EQUITIES","AAM · 量化研究 · 港股")}</div>
<h1 style="margin:.2rem 0 .25rem 0">{tr("V28-U R1.9 Signal Dashboard","V28-U R1.9 信号看板")}</h1>
<div class="small-note">{tr("Latest signal date","最新信号日期")}: <b>{latest_label}</b> &nbsp;·&nbsp; {tr("Cross-sectional 2–5 day ranking system","2–5 日横截面排序系统")} &nbsp;·&nbsp; {tr("Internal team use","团队内部使用")}</div></div>""",
    unsafe_allow_html=True
)

if page=="Daily Dashboard":
    if watch.empty:
        st.warning(tr("No latest watchlist found. Run the daily sync script after model scoring.","未找到最新观察名单。请在模型每日打分完成后运行同步脚本。"))
        st.stop()

    topn=len(watch)
    strong=int((watch.get("signal_label",pd.Series(dtype=str))=="STRONG_BUY").sum())
    mean_score=watch["signal_score"].mean() if "signal_score" in watch else np.nan
    med_adv=watch["adv20_hkd"].median() if "adv20_hkd" in watch else np.nan
    c1,c2,c3,c4=st.columns(4)
    c1.metric(tr("Watchlist","观察名单"), f"{topn} names")
    c2.metric("STRONG_BUY", f"{strong}")
    c3.metric(tr("Mean signal score","平均信号分"), f"{mean_score:.1f}" if pd.notna(mean_score) else "—")
    c4.metric(tr("Median ADV20","ADV20 中位数"), hk_money(med_adv))

    st.subheader(tr("Today's ranked watchlist","今日排序观察名单"))
    display=watch.copy()
    rename={
        "watch_rank":tr("Rank","排名"),
        "code":tr("Ticker","代码"),
        "security_name":tr("Name","名称"),
        "signal_label":tr("Signal","信号"),
        "signal_score":tr("Signal Score","信号分"),
        "selection_score":tr("Selection","选择分数"),
        "preferred_horizon_days":tr("Preferred H","偏好期限"),
        "policy_pred_abs_return":tr("Pred. Return","预测收益"),
        "adv20_hkd":"ADV20",
        "market_cap_hkd":tr("Market Cap","市值")
    }
    keep=[c for c in rename if c in display.columns]
    table=display[keep].rename(columns=rename)
    pred_col=tr("Pred. Return","预测收益")
    if pred_col in table: table[pred_col]=table[pred_col].map(lambda x: pct(x))
    if "ADV20" in table: table["ADV20"]=table["ADV20"].map(hk_money)
    mcap_col=tr("Market Cap","市值")
    if mcap_col in table: table[mcap_col]=table[mcap_col].map(hk_money)
    st.dataframe(table, use_container_width=True, hide_index=True, height=590)

    left,right=st.columns([1.15,1])
    with left:
        st.subheader(tr("Cross-horizon selection profile","跨期限选择分数"))
        hcols=[f"selection_score_{h}d" for h in [2,3,4,5] if f"selection_score_{h}d" in watch]
        if hcols:
            chart=watch.head(10)[["code"]+hcols].melt("code",var_name="Horizon",value_name="Score")
            chart["Horizon"]=chart["Horizon"].str.extract(r"(\d+d)")[0]
            fig=px.line(chart,x="Horizon",y="Score",color="code",markers=True)
            fig.update_layout(height=390,legend_title_text="Ticker",margin=dict(l=10,r=10,t=20,b=10))
            st.plotly_chart(fig,use_container_width=True)
    with right:
        st.subheader(tr("Signal score distribution","信号分分布"))
        if "signal_score" in watch:
            fig=px.bar(watch.sort_values("signal_score"),x="signal_score",y="code",orientation="h",
                       labels={"signal_score":tr("Signal score","信号分"),"code":""})
            fig.update_layout(height=390,showlegend=False,margin=dict(l=10,r=10,t=20,b=10))
            st.plotly_chart(fig,use_container_width=True)

elif page=="Signal Explorer":
    if watch.empty:
        st.warning(tr("No latest watchlist available.","暂无最新观察名单。")); st.stop()
    tickers=watch["code"].astype(str).tolist()
    ticker=st.selectbox(tr("Select security","选择股票"),tickers,index=0)
    row=watch[watch["code"].astype(str).eq(ticker)].iloc[0]
    rank=row.get("watch_rank",row.get("rank",np.nan))
    a,b,c,d=st.columns(4)
    a.metric(tr("Watch rank","观察名单排名"), f"#{int(rank)}" if pd.notna(rank) else "—")
    b.metric(tr("Signal score","信号分"), f"{row.get('signal_score',np.nan):.1f}" if pd.notna(row.get("signal_score",np.nan)) else "—")
    c.metric(tr("Preferred horizon","偏好期限"), f"{int(row.get('preferred_horizon_days'))}D" if pd.notna(row.get("preferred_horizon_days",np.nan)) else "—")
    d.metric(tr("Model label","模型标签"), str(row.get("signal_label","—")))

    l,r=st.columns([1.15,1])
    with l:
        hs=[2,3,4,5]
        vals=[row.get(f"selection_score_{h}d",np.nan) for h in hs]
        fig=go.Figure(go.Bar(x=[f"{h}D" for h in hs],y=vals))
        fig.update_layout(title=tr("Selection score by horizon","各期限选择分数"),height=350,margin=dict(l=10,r=10,t=45,b=10),yaxis_title="Score")
        st.plotly_chart(fig,use_container_width=True)
    with r:
        components=pd.DataFrame({
            "Component":["H5 rank","Rank head (2D)","Residual head (2D)"],
            "Value":[row.get("h5_hold25_rank_pct",np.nan),row.get("c1_pred_rank_excess_2d",np.nan),row.get("c1_pred_resid_2d",np.nan)]
        }).dropna()
        fig=px.bar(components,x="Value",y="Component",orientation="h",title=tr("Selected model diagnostics","模型诊断"))
        fig.update_layout(height=350,margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig,use_container_width=True)

    st.subheader(tr("Technical setup diagnostics","技术状态诊断"))
    setup_map={
        "setup_trend_strength":"Trend strength","setup_extension_strength":"Extension",
        "setup_efficiency":"Efficiency","setup_breakout_strength":"Breakout",
        "setup_volume_confirmation":"Volume confirmation","setup_acceleration":"Acceleration"
    }
    setup=pd.DataFrame({tr("Dimension","维度"):[v for k,v in setup_map.items() if k in watch],
                        "Value":[row.get(k,np.nan) for k in setup_map if k in watch]}).dropna()
    if not setup.empty:
        fig=px.bar(setup,x=tr("Dimension","维度"),y="Value")
        fig.update_layout(height=330,margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig,use_container_width=True)
    st.caption(tr("Signal Score is a same-day cross-sectional percentile rank, not an upside probability.","Signal Score 是当日横截面百分位排名，不是上涨概率。"))

elif page=="Market & Validation":
    dev=summary.get("dev_validation_metrics",{})
    st.subheader(tr("Development validation snapshot","开发验证快照"))
    a,b,c,d=st.columns(4)
    a.metric(tr("H5 / excess IC","H5 / 超额收益 IC"), num(dev.get("mean_h5_ic_excess"),4))
    b.metric(tr("Residual IC","Residual IC"), num(dev.get("mean_c1_ic_resid"),4))
    c.metric(tr("Watchlist mean return","观察名单平均收益"), pct(dev.get("mean_watch_stock_return"),3))
    d.metric(tr("Watchlist – universe","观察名单 – 股票池"), pct(dev.get("mean_watch_minus_universe_stock"),3))

    if not snap.empty and "date" in snap:
        s=snap.copy(); s["date"]=pd.to_datetime(s["date"],errors="coerce")
        candidates=[c for c in ["watch_minus_universe_stock","watch_mean_stock_return","h5_ic_excess","c1_ic_resid"] if c in s]
        metric=st.selectbox(tr("Daily validation series","每日验证序列"),candidates,format_func=lambda x:{
            "watch_minus_universe_stock":tr("Watchlist minus universe","观察名单减股票池"),
            "watch_mean_stock_return":tr("Watchlist mean return","观察名单平均收益"),
            "h5_ic_excess":"H5 excess IC","c1_ic_resid":tr("Residual IC","Residual IC")}.get(x,x))
        fig=px.line(s,x="date",y=metric)
        fig.add_hline(y=0,line_width=1,line_dash="dot")
        fig.update_layout(height=420,margin=dict(l=10,r=10,t=20,b=10),xaxis_title="",yaxis_title="")
        st.plotly_chart(fig,use_container_width=True)
    st.caption(tr("June–August 2026 is labeled development validation in the supplied R1.9 result package.","所提供 R1.9 结果包中，2026 年 6–8 月标记为开发验证期。"))

elif page=="Model Architecture":
    st.subheader(tr("How R1.9 produces the daily ranking","R1.9 如何生成每日排序"))
    st.markdown(tr(
"""**1. Market state** — 56 regime variables describe HSI/HSTECH/HSCE/HSCI, market breadth, dispersion, turnover and IPO environment.

**2. Stock state** — the 97D child backbone combines those 56 market variables with 41 stock technical-state variables covering trend acceleration, trend quality, price–volume and price location.

**3. Three complementary ranking sources** — Frozen H5 acts as the stable anchor; the Rank head predicts future cross-sectional excess-return rank; the Residual head targets stock-specific return after estimated market beta.

**4. Two-stage fusion** — within each horizon: **45% H5 + 35% Rank + 20% Residual**. Across horizons: **40% 2D + 30% 3D + 20% 4D + 10% 5D**.

**5. Tradability & output** — U4 filters for market cap, liquidity, trading continuity, price and turnover stability. The eligible universe is ranked daily; Top 20 becomes the watchlist and Top 1–5 is labeled STRONG_BUY.""",
"""**1. 市场状态** — 56 个 Regime 变量描述 HSI/HSTECH/HSCE/HSCI、市场宽度、分化、换手与 IPO 环境。

**2. 个股状态** — 97D Child Backbone 由 56 个市场状态变量与 41 个个股技术状态变量组成，覆盖趋势加速、趋势质量、价量关系与价格位置。

**3. 三类互补排序来源** — Frozen H5 作为稳定锚；Rank Head 预测未来横截面超额收益排名；Residual Head 预测扣除估计市场 Beta 后的个股特异收益。

**4. 两级融合** — 单期限内：**45% H5 + 35% Rank + 20% Residual**。跨期限：**40% 2D + 30% 3D + 20% 4D + 10% 5D**。

**5. 可交易性与输出** — U4 按市值、流动性、交易连续性、股价与成交稳定性进行过滤。合格股票每日排序，Top20 进入观察名单，Top1–5 标记为 STRONG_BUY。"""
    ))
    c1,c2,c3=st.columns(3)
    c1.info("**Frozen H5**\n\n78-dimensional stable anchor")
    c2.info("**97D Child**\n\n56 market regime + 41 stock state")
    c3.info("**Final output**\n\nCross-sectional Signal Score + Top 20")
    st.subheader(tr("Weight map","权重结构"))
    weights=pd.DataFrame({"Layer":["H5","Rank","Residual","2D","3D","4D","5D"],
                          "Weight":[45,35,20,40,30,20,10],
                          "Group":["Single-horizon fusion"]*3+["Multi-horizon fusion"]*4})
    fig=px.bar(weights,x="Weight",y="Layer",orientation="h",facet_col="Group",facet_col_wrap=2,text="Weight")
    fig.update_layout(height=360,margin=dict(l=10,r=10,t=25,b=10),showlegend=False)
    st.plotly_chart(fig,use_container_width=True)

elif page=="Research Evidence":
    st.subheader(tr("TRAIN-only feature-family evidence","仅 TRAIN 样本的因子族证据"))
    if not ablation.empty:
        cols=[c for c in ["variant","feature_count","mean_selection_ic_p4","mean_precision_at_20","mean_top20_minus_universe_p4","family"] if c in ablation]
        st.dataframe(ablation[cols],use_container_width=True,hide_index=True)
        if "mean_selection_ic_p4" in ablation:
            fig=px.bar(ablation,x="mean_selection_ic_p4",y="variant",orientation="h",
                       labels={"mean_selection_ic_p4":"Mean selection IC","variant":""})
            fig.update_layout(height=330,margin=dict(l=10,r=10,t=20,b=10))
            st.plotly_chart(fig,use_container_width=True)
    if not state_diag.empty:
        st.subheader(tr("H5 top-decile state diagnostics","H5 前十分位状态诊断"))
        split=st.selectbox(tr("Evidence split","证据样本"),state_diag["split"].dropna().unique().tolist())
        d=state_diag[state_diag["split"].eq(split)]
        dim=st.selectbox(tr("Dimension","维度"),d["dimension"].dropna().unique().tolist())
        d=d[d["dimension"].eq(dim)]
        value=st.selectbox(tr("Residual horizon","Residual 期限"),[c for c in ["mean_resid_2d","mean_resid_3d","mean_resid_5d"] if c in d])
        fig=px.bar(d,x="bucket",y=value)
        fig.update_layout(height=350,margin=dict(l=10,r=10,t=20,b=10),xaxis_title="",yaxis_title=value)
        st.plotly_chart(fig,use_container_width=True)

st.divider()
st.caption(tr("V28-U Signal Engine R1.9 · Internal quantitative research dashboard · Data refreshes from the model output files committed/synced to dashboard_data.","V28-U Signal Engine R1.9 · 内部量化研究看板 · 数据由同步至 dashboard_data 的模型输出更新。"))
