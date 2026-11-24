from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="YouTube kanal dashboard", page_icon="📊", layout="wide")

TEAL, DARK, RED, GREEN = "#01B8AA", "#374649", "#FD625E", "#5CB85C"
PINK, PINK_LINE = "rgba(240,138,138,0.35)", "#E0504F"
OY = {1: "Yan", 2: "Fev", 3: "Mar", 4: "Apr", 5: "May", 6: "Iyn"}
TUR_RANG = {"Video": TEAL, "Shorts": DARK, "Jonli efir": RED}
MAVZU_RANG = {"Python": "#3776AB", "Excel": "#1D6F42", "SQL": "#E48E00", "Power BI": "#C9A800"}

st.markdown(
    """
    <style>
    .block-container{padding-top:1.2rem}
    h1.title{text-align:center;font-weight:300;font-size:2.6rem;margin:0 0 .6rem}
    .big{text-align:center;font-size:2.8rem;font-weight:300;color:#E0504F;line-height:1.1}
    </style>
    """,
    unsafe_allow_html=True,
)


def show(fig, key):
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:  # eski Streamlit versiyalari uchun
        st.plotly_chart(fig, use_container_width=True, key=key)


@st.cache_data
def load(src):
    return pd.read_excel(src)


# ---------- Ma'lumot ----------
upload = st.sidebar.file_uploader("youtube.xlsx faylini yuklang", type="xlsx")
if upload is not None:
    df = load(upload)
elif Path("youtube.xlsx").exists():
    df = load("youtube.xlsx")
else:
    st.info("youtube.xlsx faylini chap paneldan yuklang yoki app.py bilan bir papkaga qo'ying.")
    st.stop()

# ---------- Filtrlar (Power BI slicer) ----------
st.sidebar.header("Filtrlar")
oy_lo, oy_hi = st.sidebar.slider("Oylar", 1, 6, (1, 6))
mavzular = st.sidebar.multiselect("Mavzu", sorted(df["mavzu"].unique()), default=sorted(df["mavzu"].unique()))
turlar = st.sidebar.multiselect("Video turi", ["Video", "Shorts", "Jonli efir"], default=["Video", "Shorts", "Jonli efir"])

f = df[df["oy"].between(oy_lo, oy_hi) & df["mavzu"].isin(mavzular) & df["tur"].isin(turlar)]

st.markdown('<h1 class="title">Umumiy ko\'rinish</h1>', unsafe_allow_html=True)
if f.empty:
    st.warning("Tanlangan filtrlar bo'yicha ma'lumot yo'q.")
    st.stop()
st.caption(f"Sana: {f['sana'].min():%d.%m.%Y} – {f['sana'].max():%d.%m.%Y} · {len(f)} ta video")

oylar = list(range(oy_lo, oy_hi + 1))
lab = [OY[o] for o in oylar]
m = f.groupby("oy")[["korishlar", "layklar", "izohlar"]].sum().reindex(oylar, fill_value=0)

tab1, tab2 = st.tabs(["📊 Dashboard", "🧊 3D ko'rinish"])

# =================== DASHBOARD ===================
with tab1:
    c1, c2, c3 = st.columns([1, 1.5, 1.3])

    def kpi(col, title, num, den, key):
        with col.container(border=True):
            r = (num / den.replace(0, pd.NA) * 100).astype(float).fillna(0)
            total = num.sum() / den.sum() * 100
            st.caption(title)
            st.markdown(f'<div class="big">{total:.1f} %</div>'.replace(".", ","), unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(x=lab, y=r, fill="tozeroy", fillcolor=PINK,
                                       line=dict(color=PINK_LINE, width=1.5, shape="spline"),
                                       hovertemplate="%{x}: %{y:.2f}%<extra></extra>"))
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False, rangemode="tozero")
            fig.update_layout(height=110)
            show(fig, key)

    kpi(c1, "Layk / ko'rish, %", m["layklar"], m["korishlar"], "k1")
    kpi(c1, "Izoh / ko'rish, %", m["izohlar"], m["korishlar"], "k2")

    with c2.container(border=True):
        st.caption("Ko'rishlar va layklar (oylar bo'yicha)")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=lab, y=m["korishlar"], name="Ko'rishlar", marker_color=TEAL)
        fig.add_scatter(x=lab, y=m["layklar"], name="Layklar", mode="lines+markers",
                        line=dict(color=DARK, width=2), secondary_y=True)
        fig.update_layout(height=330, legend=dict(orientation="h", y=1.12))
        fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,.2)")
        fig.update_yaxes(showgrid=False, rangemode="tozero", secondary_y=True)
        show(fig, "combo")

    with c3.container(border=True):
        st.caption("Ko'rishlar o'zgarishi (oyma-oy)")
        v = m["korishlar"].tolist()
        diffs = [b - a for a, b in zip(v, v[1:])]
        fig = go.Figure(go.Waterfall(
            x=[lab[0]] + lab[1:] + ["Jami"],
            y=[v[0]] + diffs + [0],
            measure=["absolute"] + ["relative"] * len(diffs) + ["total"],
            increasing=dict(marker=dict(color=GREEN)),
            decreasing=dict(marker=dict(color=RED)),
            totals=dict(marker=dict(color=TEAL)),
            connector=dict(line=dict(color="rgba(128,128,128,.4)")),
        ))
        fig.update_layout(height=330, showlegend=False)
        fig.update_yaxes(gridcolor="rgba(128,128,128,.2)")
        show(fig, "waterfall")

    d1, d2, d3 = st.columns([1, 1.5, 1.3])

    with d1.container(border=True):
        st.caption("Ko'rishlar ulushi (video turi bo'yicha)")
        t = f.groupby("tur")["korishlar"].sum()
        fig = go.Figure(go.Pie(labels=t.index, values=t.values, textinfo="percent",
                               marker=dict(colors=[TUR_RANG[k] for k in t.index])))
        fig.update_layout(height=300, legend=dict(orientation="h", y=-0.05))
        show(fig, "pie")

    with d2.container(border=True):
        st.caption("Ko'rishlar (mavzu bo'yicha)")
        mk = f.groupby("mavzu")["korishlar"].sum().sort_values()
        fig = go.Figure(go.Bar(x=mk.values, y=mk.index, orientation="h", marker_color=TEAL,
                               text=[f"{x:,}".replace(",", " ") for x in mk.values], textposition="outside"))
        fig.update_layout(height=300)
        fig.update_xaxes(gridcolor="rgba(128,128,128,.2)", range=[0, mk.max() * 1.25])
        show(fig, "hbar")

    with d3.container(border=True):
        st.caption("Oylik ko'rishlar (tur bo'yicha, to'plangan)")
        p = f.pivot_table(index="oy", columns="tur", values="korishlar", aggfunc="sum", fill_value=0).reindex(oylar, fill_value=0)
        fig = go.Figure()
        for tname in ["Video", "Shorts", "Jonli efir"]:
            if tname in p:
                fig.add_scatter(x=lab, y=p[tname], name=tname, stackgroup="one", mode="lines",
                                line=dict(color=TUR_RANG[tname], shape="spline"))
        fig.add_scatter(x=lab, y=[m["korishlar"].mean()] * len(lab), name="O'rtacha jami", mode="lines",
                        line=dict(color="gray", dash="dash", width=1.5))
        fig.update_layout(height=300, legend=dict(orientation="h", y=1.15))
        fig.update_yaxes(gridcolor="rgba(128,128,128,.2)")
        show(fig, "area")

# =================== 3D ===================
with tab2:
    tur3d = st.radio("3D diagramma turi", ["3D ustunlar", "3D sirt", "3D pufakchalar"], horizontal=True)
    order = [x for x in ["Power BI", "SQL", "Excel", "Python"] if x in mavzular]  # Python orqada
    V = f.pivot_table(index="oy", columns="mavzu", values="korishlar", aggfunc="sum", fill_value=0).reindex(index=oylar, columns=order, fill_value=0)
    L = f.pivot_table(index="oy", columns="mavzu", values="layklar", aggfunc="sum", fill_value=0).reindex(index=oylar, columns=order, fill_value=0)

    scene = dict(
        xaxis=dict(title="Oy", tickvals=list(range(len(oylar))), ticktext=lab),
        yaxis=dict(title="Mavzu", tickvals=list(range(len(order))), ticktext=order),
        zaxis=dict(title="Ko'rishlar"),
        camera=dict(eye=dict(x=1.6, y=-1.7, z=0.9)),
    )

    def cuboid(x, y, h, w=0.6):
        vx = [x, x, x + w, x + w, x, x, x + w, x + w]
        vy = [y, y + w, y + w, y, y, y + w, y + w, y]
        vz = [0, 0, 0, 0, h, h, h, h]
        return vx, vy, vz

    fig = go.Figure()
    if tur3d == "3D ustunlar":
        I = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        J = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        K = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        for j, mv in enumerate(order):
            X, Y, Z, II, JJ, KK = [], [], [], [], [], []
            for i, o in enumerate(oylar):
                vx, vy, vz = cuboid(i, j, float(V.loc[o, mv]))
                off = len(X)
                X += vx; Y += vy; Z += vz
                II += [a + off for a in I]; JJ += [a + off for a in J]; KK += [a + off for a in K]
            fig.add_trace(go.Mesh3d(x=X, y=Y, z=Z, i=II, j=JJ, k=KK, color=MAVZU_RANG[mv],
                                    flatshading=True, name=mv, showlegend=True, hoverinfo="name"))
    elif tur3d == "3D sirt":
        if len(oylar) < 2 or len(order) < 2:
            st.info("Sirt uchun kamida 2 oy va 2 mavzu tanlang.")
        else:
            fig.add_trace(go.Surface(z=V.T.values, x=list(range(len(oylar))), y=list(range(len(order))),
                                     colorscale="Viridis", colorbar=dict(title="Ko'rish")))
    else:
        for j, mv in enumerate(order):
            fig.add_trace(go.Scatter3d(
                x=list(range(len(oylar))), y=[j] * len(oylar), z=V[mv].values, mode="markers", name=mv,
                marker=dict(size=(L[mv].values / L.values.max() * 28 + 6), color=MAVZU_RANG[mv],
                            line=dict(color="white", width=1)),
                customdata=L[mv].values,
                hovertemplate=mv + "<br>Ko'rish: %{z:,}<br>Layk: %{customdata:,}<extra></extra>"))
        st.caption("Balandlik = ko'rishlar, pufak o'lchami = layklar")
    fig.update_layout(scene=scene, height=640, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", y=1.02), paper_bgcolor="rgba(0,0,0,0)")
    try:
        st.plotly_chart(fig, width="stretch", key="d3")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key="d3")
