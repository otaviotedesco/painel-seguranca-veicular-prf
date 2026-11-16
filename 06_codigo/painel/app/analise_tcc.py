import json, pathlib
import numpy as np
import pandas as pd, streamlit as st, plotly.express as px, plotly.graph_objects as go
import estilo

R = pathlib.Path(__file__).resolve().parents[3]
TAB = R / "08_resultados" / "tabelas" / "fase06"
FLUXO = R / "03_dados" / "08_populacao" / "fluxograma_inclusao.json"
GER = R / "08_resultados" / "tabelas" / "geracoes" / "GERACOES_v1_completa.csv"
PLAT = R / "08_resultados" / "tabelas" / "geracoes" / "PLATAFORMAS_COMPARTILHADAS_v1.csv"
MARCA = ("_TRANSICAO", "_CONFLITO", "_SEM_GERACAO")

ESTRATO = {"auto_sozinho": "Automóvel sozinho", "auto x leve": "× veículo leve", "auto x moto": "× moto",
           "auto x pesado": "× caminhão", "auto x onibus": "× ônibus", "auto x bicicleta": "× bicicleta",
           "auto x multiplos": "× vários tipos", "auto x outro": "× outro veículo"}
FAIXAS = ["<2000", "2000-2009", "2010-2014", "2015-2019", "2020+"]
PAPEL = {"Condutor": "Condutor", "Passageiro": "Passageiro"}


def n(v): return f"{int(round(v)):,}".replace(",", ".")
def p(v, c=1): return f"{v:.{c}f}".replace(".", ",") + "%"


@st.cache_data(show_spinner=False)
def ler(nome):
    return pd.read_csv(TAB / nome, sep=";")


@st.cache_data(show_spinner=False)
def nomes_geracao():
    g = pd.read_csv(GER, sep=";", dtype=str, keep_default_na=False)
    return {k: f"{f} · {nm}" for k, f, nm in zip(g.geracao_id, g.familia, g.nome)}


def rotulo(u):
    for m in MARCA:
        if u.endswith(m): return u[: -len(m)] + " · " + {"_TRANSICAO": "geração ambígua", "_CONFLITO": "texto e ano em conflito",
                                                         "_SEM_GERACAO": "sem geração"}[m]
    return nomes_geracao().get(u, u)


def grafico(fig, altura=420):
    fig.update_layout(height=altura, margin=dict(l=10, r=10, t=30, b=10),
                      template=estilo.TEMPLATE, font=dict(size=13))
    st.plotly_chart(fig, width="stretch")


def barras_ic(d, rotulo, ordem=None, altura=380):
    d = d.copy()
    d["rot"] = d[rotulo]
    fig = go.Figure(go.Bar(
        y=d.rot, x=d.pct_grave, orientation="h", marker_color=estilo.COR_PRINCIPAL,
        error_x=dict(type="data", symmetric=False, array=d.ic95_sup - d.pct_grave,
                     arrayminus=d.pct_grave - d.ic95_inf, color="#555"),
        customdata=d[["n"]].values,
        hovertemplate="%{y}<br>%{x:.2f}% · n = %{customdata[0]:,}<extra></extra>"))
    fig.update_xaxes(title="% de óbito ou lesão grave entre os ocupantes", rangemode="tozero")
    if ordem: fig.update_yaxes(categoryorder="array", categoryarray=ordem[::-1])
    grafico(fig, altura)


def tela_analise_tcc():
    estilo.cabecalho("Análise do TCC",
                     "Gravidade das lesões de <b>ocupantes de automóveis</b> em sinistros registrados pela PRF nas "
                     "rodovias federais, <b>2019 a 2025</b>, segundo o modelo e o ano de fabricação do veículo. "
                     "As abas seguem a ordem do trabalho: quem entra na análise, os fatores que mais alteram a "
                     "gravidade, o contexto por UF, a comparação entre modelos e a verificação.",
                     "Resultados do trabalho")
    st.warning("**Como ler esta tela.** Os números descrevem o que aconteceu **depois que o sinistro ocorreu**. "
               "Não há dado de quantos carros de cada modelo circulam nem de quantos quilômetros rodam; por isso "
               "nada aqui indica que um modelo se envolve mais em sinistros ou que seja intrinsecamente mais seguro. "
               "Diferenças são associações, não causas.", icon="⚠️")
    if not TAB.exists() or not FLUXO.exists():
        st.error("Os resultados da análise não estão disponíveis.")
        return
    st.caption("Os números desta tela são os resultados apresentados no texto do TCC. "
               "Na Consulta livre, o filtro \"Recorte do TCC\" reproduz exatamente esta população.")

    abas = st.tabs(["População", "Fatores além do modelo", "Por UF", "Entre modelos", "Verificação"])

    with abas[0]:
        fl = json.load(open(FLUXO, encoding="utf-8"))
        tot = {k: sum(x[k] for x in fl) for k in fl[0] if k != "ano"}
        c = st.columns(4)
        c[0].metric("Ocupantes", n(tot["5_modelo_identificado"]))
        c[1].metric("Automóveis", n(tot["5_automoveis"]))
        c[2].metric("Sinistros", n(tot["5_sinistros"]))
        c[3].metric("Óbito ou lesão grave", p(100 * tot["6_obito_ou_grave"] / tot["5_modelo_identificado"], 2))
        etapas = [("Pessoas registradas na janela", "0_pessoas"), ("Ocupantes (condutor ou passageiro)", "1_ocupantes"),
                  ("Em automóvel", "2_em_automovel"), ("Com desfecho conhecido", "3_desfecho_conhecido"),
                  ("Com ano de fabricação válido", "4_ano_fab_valido"), ("Com modelo identificado", "5_modelo_identificado")]
        f = pd.DataFrame([{"Etapa": e, "Restam": tot[k]} for e, k in etapas])
        f["Retirados"] = (-f.Restam.diff()).fillna(0).astype(int)
        st.subheader("Quem entra na análise")
        st.dataframe(f.assign(Restam=f.Restam.map(n), Retirados=f.Retirados.map(lambda v: n(v) if v else "—")),
                     hide_index=True, width="stretch")
        st.caption("Os registros retirados continuam na base e na Consulta livre; só não entram na comparação.")

    with abas[1]:
        st.markdown("Antes de comparar modelos: o tipo de colisão, a idade do veículo, o papel do ocupante e o tipo de via "
                    "mudam a gravidade mais do que o modelo do carro. Por isso toda comparação entre modelos é feita **dentro** "
                    "do mesmo tipo de colisão e da mesma faixa de fabricação, e a verificação controla também o contexto da via.")
        e = ler("marginal_por_estrato.csv"); e["Tipo de colisão"] = e.estrato.map(ESTRATO).fillna(e.estrato)
        st.subheader("Tipo de colisão")
        barras_ic(e.sort_values("pct_grave", ascending=False), "Tipo de colisão")
        fx = ler("marginal_por_faixa_ano.csv"); fx["Faixa de fabricação"] = fx.faixa_ano_fab
        st.subheader("Ano de fabricação do veículo")
        barras_ic(fx, "Faixa de fabricação", ordem=FAIXAS, altura=300)
        pa = ler("marginal_por_papel.csv"); pa["Papel"] = pa.tipo_envolvido
        st.subheader("Condutor ou passageiro")
        barras_ic(pa, "Papel", altura=220)
        st.subheader("Contexto da via")
        tp = ler("marginal_por_tipo_pista.csv"); tp["Tipo de pista"] = tp.tipo_pista
        barras_ic(tp, "Tipo de pista", ordem=["Simples", "Dupla", "Múltipla"], altura=240)
        us = ler("marginal_por_uso_solo.csv"); us["Trecho"] = us.uso_solo.map({"rural": "Rural", "urbano": "Urbano"}).fillna(us.uso_solo)
        barras_ic(us, "Trecho", altura=200)
        st.caption("Tipo de pista e trecho urbano ou rural são características do local do sinistro, usadas como contexto, "
                   "não como causa.")
        st.caption("IC95% de Wilson; não corrige a dependência entre ocupantes do mesmo sinistro (a verificação corrige).")

    with abas[2]:
        u = ler("gravidade_por_uf.csv")
        medida = st.radio("Medida", ["Observada", "Padronizada pelo tipo de colisão"], horizontal=True, key="tcc_uf")
        col = "pct_grave" if medida == "Observada" else "pct_grave_padronizada_estrato"
        u = u.sort_values(col, ascending=False)
        fig = px.bar(u, x="uf", y=col, labels={"uf": "UF do sinistro", col: "% de óbito ou lesão grave"},
                     hover_data={"n": True}, color_discrete_sequence=[estilo.COR_PRINCIPAL])
        if col == "pct_grave":
            fig.update_traces(error_y=dict(type="data", symmetric=False, array=u.ic95_sup - u.pct_grave,
                                           arrayminus=u.pct_grave - u.ic95_inf, color="#555"))
        grafico(fig, 380)
        st.info("UF é o local do sinistro, não onde o ocupante mora. O mapa descreve o **contexto** dos sinistros, não os "
                "veículos: a diferença entre estados não se explica pelo tipo de colisão, e cerca de 30% dela acompanha o tipo "
                "de pista e o trecho urbano ou rural. Velocidade, tempo de atendimento e prática de registro são explicações "
                "possíveis que os dados não medem. Por isso tipo de pista, trecho e UF entram juntos como controle na "
                "verificação entre modelos.", icon="ℹ️")

    with abas[3]:
        cel = ler("celulas_unidade_faixa_estrato.csv"); cel["Modelo"] = cel.unidade.map(rotulo)
        c1, c2 = st.columns(2)
        fx_ = c1.selectbox("Faixa de fabricação", FAIXAS, index=2, key="tcc_fx")
        est_ops = [k for k in ESTRATO if k in set(cel.estrato)]
        es_ = c2.selectbox("Tipo de colisão", est_ops, format_func=lambda k: ESTRATO[k], key="tcc_es")
        d = cel[(cel.faixa_ano_fab == fx_) & (cel.estrato == es_)].copy()
        comp = d[d.comparavel.astype(str).isin(["True", "true"])].sort_values("pct_grave", ascending=False)
        amb = d[d.unidade.str.endswith(MARCA)]
        st.caption(f"{len(comp)} modelos (modelo + geração) com ao menos 300 ocupantes nesta combinação, de {len(d)} presentes "
                   f"({n(comp.n.sum())} de {n(d.n.sum())} ocupantes). "
                   + (f"{n(amb.n.sum())} ocupantes estão em carros cujo ano de fabricação cabe em duas gerações; "
                      "eles aparecem na tabela abaixo, mas não entram na comparação." if len(amb) else ""))
        if comp.empty:
            st.info("Nenhum modelo alcança 300 ocupantes nesta combinação: não há comparação a fazer aqui.")
        else:
            barras_ic(comp, "Modelo", ordem=comp.Modelo.tolist(), altura=max(260, 26 * len(comp)))
        st.warning("Leia a **existência e o tamanho** da diferença, não a posição exata. Retirando 2024 ou contando por "
                   "veículo, a ordem geral se mantém, mas o modelo exato do topo ou do fundo de uma combinação pode trocar. "
                   "Parte da diferença é massa e perfil de uso, que o nome do modelo apenas indica. "
                   "A geração segue a plataforma do veículo; reestilizações sobre a mesma plataforma contam como a mesma geração.", icon="⚠️")
        if PLAT.exists():
            with st.expander("Modelos diferentes que compartilham a mesma plataforma"):
                pl = pd.read_csv(PLAT, sep=";", dtype=str, keep_default_na=False)
                st.caption("Cada modelo é comparado com seu próprio nome, como é vendido e registrado. "
                           "Esta tabela mostra, apenas como informação, quais deles foram construídos sobre a mesma "
                           "plataforma, segundo a tabela de gerações validada pelo autor. Nenhum resultado é "
                           "recalculado por plataforma.")
                pl["Modelo"] = pl.familia + " · " + pl.nome + pl.base.map({"inferencia": " *"}).fillna("")
                t = (pl.groupby("plataforma", sort=False)
                       .agg(Modelos=("Modelo", lambda x: "; ".join(x)), Famílias=("familia", "nunique"))
                       .reset_index().rename(columns={"plataforma": "Plataforma"}))
                st.dataframe(t, hide_index=True, width="stretch")
                if (pl.base == "inferencia").any():
                    st.caption("* Plataforma atribuída por semelhança de nome na tabela de gerações; "
                               "agrupamento ainda em conferência.")
        with st.expander("Todos os modelos desta combinação, inclusive abaixo de 300 ocupantes"):
            st.dataframe(d.sort_values("n", ascending=False)[["Modelo", "n", "pct_grave", "ic95_inf", "ic95_sup", "pct_obito", "comparavel"]]
                         .rename(columns={"pct_grave": "% óbito ou grave", "pct_obito": "% óbito",
                                          "comparavel": "n ≥ 300"}), hide_index=True, width="stretch")

    with abas[4]:
        st.markdown("Uma regressão logística confere se as diferenças entre modelos resistem quando se controlam, ao mesmo tempo, "
                    "faixa de fabricação, tipo de colisão, sexo, idade e papel do ocupante, tipo de pista, trecho urbano ou rural e UF. "
                    "Cada valor compara o modelo com o **Gol G5–G8** (o Novo Gol, de 2008 em diante): "
                    "abaixo de 1, menor chance de óbito ou lesão grave; acima de 1, maior.")
        f = ler("logistica_leitura.csv")
        f["Modelo"] = f.unidade.map(rotulo)
        nd, nb, nh = (f.leitura == "difere").sum(), f.bonferroni.sum(), f.benjamini_hochberg.sum()
        so_sig = st.checkbox("Mostrar só os modelos que diferem do Gol G5–G8", value=True, key="tcc_sig")
        if so_sig: f = f[f.leitura == "difere"]
        f = f.sort_values("or")
        f["Leitura"] = np.select([f.bonferroni, f.benjamini_hochberg, f.leitura == "difere",
                                  f.leitura == "depende do contexto"],
                                 ["difere; resiste às duas correções", "difere; resiste só a Benjamini-Hochberg",
                                  "difere a 5%; não resiste às correções", "depende do controle de pista e trecho"],
                                 "não difere da referência")
        fig = go.Figure(go.Scatter(x=f["or"], y=f.Modelo, mode="markers", marker=dict(color=estilo.AZUL, size=8),
                                   error_x=dict(type="data", symmetric=False, array=f.or_ic_sup - f["or"],
                                                arrayminus=f["or"] - f.or_ic_inf, color="#555"),
                                   customdata=f[["Leitura"]].values,
                                   hovertemplate="%{y}: %{x:.2f}<br>%{customdata[0]}<extra></extra>"))
        fig.add_vline(x=1, line_dash="dash", line_color="#888")
        fig.update_xaxes(title="Razão de chances contra o Gol G5–G8 (IC95%, agrupado por sinistro)", type="log")
        grafico(fig, max(320, 20 * len(f)))
        st.caption(f"{nd} de {len(ler('logistica_leitura.csv'))} modelos diferem da referência ao nível de 5%; "
                   f"{nb} resistem à correção de Bonferroni e {nh} à de Benjamini-Hochberg para comparações múltiplas. "
                   "Dois modelos (Palio 1ª geração e 206) só diferem com o controle de pista e trecho e não são "
                   "contados como diferentes. Passe o mouse sobre um ponto para ver a leitura.")
        s = ler("sensibilidade_leitura.csv")
        r = s.groupby("sensibilidade").spearman.median()
        st.caption(f"Robustez da ordem entre modelos (correlação de Spearman, mediana entre combinações): "
                   f"sem 2024 {r.get('sem_2024', float('nan')):.2f} · contando por veículo {r.get('unidade_veiculo', float('nan')):.2f}.")
