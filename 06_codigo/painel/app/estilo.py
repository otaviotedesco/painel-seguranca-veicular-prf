"""Identidade visual do painel (DP-52). So aparencia: nenhum dado, calculo ou filtro e definido aqui.

- Paleta de interface sobria (azul-marinho, cinzas) e paleta categorica dos graficos validada para
  daltonismo (skill dataviz, paleta de referencia: ordem fixa, ΔE CVD adjacente >= 9,1).
- Template Plotly "tcc" aplicado como padrao a todos os graficos; cores com significado proprio
  (desfecho, IC) continuam definidas onde ja estavam.
- Componentes: cabecalho de pagina, titulo de secao com descricao, cards de indicador.
"""
import streamlit as st, plotly.graph_objects as go, plotly.io as pio

AZUL = "#1F3A5F"          # cor institucional: titulos, navegacao, botao principal
AZUL_CLARO = "#E8EEF5"
TINTA = "#1F2933"; TINTA_2 = "#52606D"; TINTA_3 = "#7B8794"
BORDA = "#E4E7EB"; FUNDO_2 = "#F5F7FA"
SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COR_PRINCIPAL = SERIE[0]  # graficos de uma serie so

pio.templates["tcc"] = go.layout.Template(layout=dict(
    font=dict(family="Source Sans Pro, Segoe UI, system-ui, sans-serif", size=13, color=TINTA),
    title=dict(font=dict(size=16, color=TINTA), x=0, xanchor="left"),
    colorway=SERIE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="#EEF0F2", linecolor="#CBD2D9", zerolinecolor="#CBD2D9", tickcolor="#CBD2D9"),
    yaxis=dict(gridcolor="#EEF0F2", linecolor="#CBD2D9", zerolinecolor="#CBD2D9", tickcolor="#CBD2D9"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12, color=TINTA_2)),
    hoverlabel=dict(bgcolor="white", bordercolor=BORDA, font=dict(color=TINTA)),
    margin=dict(l=10, r=10, t=50, b=10)))
TEMPLATE = "plotly_white+tcc"
pio.templates.default = TEMPLATE

CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: "Source Sans Pro", "Segoe UI", system-ui, sans-serif; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }}
h1 {{ color: {AZUL}; font-weight: 700; letter-spacing: -0.01em; }}
h2, h3 {{ color: {TINTA}; font-weight: 600; }}
[data-testid="stSidebar"] {{ background: {FUNDO_2}; border-right: 1px solid {BORDA}; }}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ font-size: 0.95rem; color: {TINTA_2};
    text-transform: uppercase; letter-spacing: 0.04em; margin-top: 1rem; }}
[data-testid="stMetric"] {{ background: white; border: 1px solid {BORDA}; border-radius: 10px;
    padding: 0.8rem 1rem; }}
[data-testid="stMetricLabel"] p {{ color: {TINTA_2}; font-size: 0.85rem; }}
[data-testid="stMetricValue"] {{ color: {AZUL}; font-size: 1.55rem; }}
[data-testid="stMetricValue"] > div {{ overflow: visible; text-overflow: clip; }}
.tcc-card.nav {{ min-height: 250px; }}
.tcc-marca {{ font-size: 0.78rem; color: {TINTA_3}; line-height: 1.35; margin: -0.5rem 0 0.6rem 0; }}
.tcc-marca b {{ color: {AZUL}; font-size: 0.9rem; }}
.tcc-sobretitulo {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: {TINTA_3};
    margin-bottom: 0.2rem; }}
.tcc-sub {{ color: {TINTA_2}; font-size: 1.02rem; margin-top: -0.6rem; margin-bottom: 1.2rem; max-width: 900px; }}
.tcc-secao {{ border-top: 1px solid {BORDA}; margin-top: 1.6rem; padding-top: 1.0rem; }}
.tcc-secao h3 {{ margin: 0 0 0.15rem 0; font-size: 1.15rem; }}
.tcc-secao p {{ color: {TINTA_2}; margin: 0 0 0.6rem 0; font-size: 0.95rem; max-width: 950px; }}
.tcc-card {{ background: white; border: 1px solid {BORDA}; border-radius: 12px; padding: 1rem 1.1rem;
    height: 100%; }}
.tcc-card .rot {{ color: {TINTA_3}; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }}
.tcc-card .val {{ color: {AZUL}; font-size: 1.55rem; font-weight: 700; margin: 0.15rem 0; }}
.tcc-card .txt {{ color: {TINTA_2}; font-size: 0.92rem; line-height: 1.45; }}
.tcc-card h4 {{ color: {AZUL}; margin: 0 0 0.35rem 0; font-size: 1.02rem; }}
.tcc-hero {{ background: linear-gradient(135deg, {AZUL} 0%, #2C5282 100%); color: white; border-radius: 16px;
    padding: 2.2rem 2.4rem; margin-bottom: 1.4rem; }}
.tcc-hero .sob {{ text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.78rem; opacity: 0.8; }}
.tcc-hero h1 {{ color: white; font-size: 2.0rem; line-height: 1.2; margin: 0.4rem 0 0.6rem 0; }}
.tcc-hero .sub {{ font-size: 1.08rem; opacity: 0.92; max-width: 900px; line-height: 1.5; }}
.tcc-hero .aut {{ font-size: 0.88rem; opacity: 0.75; margin-top: 1rem; }}
.tcc-chips span {{ display: inline-block; background: {AZUL_CLARO}; color: {AZUL}; border-radius: 999px;
    padding: 0.15rem 0.65rem; margin: 0 0.35rem 0.35rem 0; font-size: 0.82rem; }}
</style>
"""

def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)

def marca_lateral():
    st.sidebar.markdown('<div class="tcc-marca"><b>Segurança veicular nas rodovias federais</b><br>'
                        'Painel do TCC · dados abertos da PRF</div>', unsafe_allow_html=True)

def cabecalho(titulo, subtitulo=None, sobretitulo=None):
    if sobretitulo:
        st.markdown(f'<div class="tcc-sobretitulo">{sobretitulo}</div>', unsafe_allow_html=True)
    st.title(titulo)
    if subtitulo:
        st.markdown(f'<div class="tcc-sub">{subtitulo}</div>', unsafe_allow_html=True)

def secao(titulo, descricao=None):
    d = f"<p>{descricao}</p>" if descricao else ""
    st.markdown(f'<div class="tcc-secao"><h3>{titulo}</h3>{d}</div>', unsafe_allow_html=True)

def card(conteudo_html, classe=""):
    st.markdown(f'<div class="tcc-card {classe}">{conteudo_html}</div>', unsafe_allow_html=True)

def card_valor(rotulo, valor, texto=""):
    card(f'<div class="rot">{rotulo}</div><div class="val">{valor}</div><div class="txt">{texto}</div>')

def chips(itens):
    st.markdown('<div class="tcc-chips">' + "".join(f"<span>{i}</span>" for i in itens) + "</div>",
                unsafe_allow_html=True)
