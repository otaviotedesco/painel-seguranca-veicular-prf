import pandas as pd, streamlit as st, plotly.express as px, plotly.graph_objects as go
import estilo

CV = "classificacao_acidente IN ('Com Vítimas Feridas', 'Com Vítimas Fatais')"
FT = "(classificacao_acidente = 'Com Vítimas Fatais')"
DIAS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
        "Sexta-feira", "Sábado", "Domingo"]
NO_GRUPO = {"bicicleta": "na bicicleta", "moto": "na moto", "leve": "no leve",
            "onibus": "no ônibus", "pesado": "no pesado"}
GRUPOS = {"bicicleta": "Bicicleta", "moto": "Moto", "leve": "Leve",
          "onibus": "Ônibus", "pesado": "Pesado"}
DESFECHO = {"ileso": "Ileso", "lesoes_leves": "Lesões leves",
            "lesoes_graves": "Lesões graves", "obito": "Óbito",
            "nao_informado": "Não informado"}
COR_DESFECHO = {"Ileso": "#9ecae1", "Lesões leves": "#fdd49e", "Lesões graves": "#fc8d59",
                "Óbito": "#b30000", "Não informado": "#d9d9d9"}


def n(v):
    return f"{int(round(v)):,}".replace(",", ".")


def p(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",") + "%"


def titulo(num, pergunta):
    st.subheader(f"{num}. {pergunta}")


def legenda(janela, base, total=None):
    extra = f" · {total}" if total else ""
    st.caption(f"Janela: {janela} · Base: {base}{extra}")


def cabecalho(num, pergunta, janela, base, total=None):
    titulo(num, pergunta)
    legenda(janela, base, total)


def como_ler(texto):
    st.markdown(f"**Como ler.** {texto}")


def cuidado(texto):
    st.info(texto, icon="ℹ️")


def grafico(fig, altura=420):
    fig.update_layout(height=altura, margin=dict(l=10, r=10, t=30, b=10),
                      template=estilo.TEMPLATE, font=dict(size=13))
    st.plotly_chart(fig, width="stretch")


def filtro_dois_veiculos(chave):
    so2 = not st.checkbox("Incluir sinistros com 3 ou mais veículos", key=chave,
                          help="Com dois veículos, o par é a própria colisão. Com três "
                               "ou mais, o par diz só que os dois estavam no mesmo sinistro.")
    return ("AND n_veiculos_sinistro = 2" if so2 else ""), \
           ("sinistros com exatamente 2 veículos" if so2 else "todos os sinistros com 2+ veículos")


def q1(consultar):
    titulo(1, "Quando um veículo leve colide com um pesado, onde fica o óbito?")
    cond, rot = filtro_dois_veiculos("q1_todos")
    d = consultar(f"""
        SELECT CASE
          WHEN severidade_veiculo = 'sem_ocupante_com_desfecho'
            OR severidade_veiculo_cp = 'sem_ocupante_com_desfecho' THEN 'Sem desfecho em um dos lados'
          WHEN severidade_veiculo = 'obito' AND severidade_veiculo_cp = 'obito' THEN 'Óbito nos dois'
          WHEN severidade_veiculo = 'obito' THEN 'Óbito só no leve'
          WHEN severidade_veiculo_cp = 'obito' THEN 'Óbito só no pesado'
          ELSE 'Nenhum óbito' END AS resultado,
          count(*) AS pares
        FROM fato_par_veiculo
        WHERE contraparte_tipo = 'veiculo' AND grupo_veiculo = 'leve'
          AND grupo_veiculo_cp = 'pesado' {cond}
        GROUP BY 1""")
    tot = d.pares.sum()
    sem = d.loc[d.resultado == "Sem desfecho em um dos lados", "pares"].sum()
    k = d[d.resultado != "Sem desfecho em um dos lados"].copy()
    base = k.pares.sum()
    k["pct"] = 100 * k.pares / base
    ordem = ["Óbito só no leve", "Óbito só no pesado", "Óbito nos dois", "Nenhum óbito"]
    k["resultado"] = pd.Categorical(k.resultado, ordem, ordered=True)
    k = k.sort_values("resultado")
    legenda("2013–2025", f"colisões leve × pesado, {rot}", f"{n(tot)} colisões")
    obito = k[k.resultado != "Nenhum óbito"]
    fig = px.bar(obito, x="resultado", y="pares", text=obito.apply(
        lambda r: f"{n(r.pares)}  ({p(r.pct, 2)})", axis=1),
        color="resultado", color_discrete_sequence=["#b30000", "#2b8cbe", "#6a51a3"],
        labels={"resultado": "", "pares": "colisões"})
    fig.update_layout(showlegend=False)
    grafico(fig, 380)
    def g(r): return int(k.loc[k.resultado == r, "pares"].sum())
    leve, pesado, dois = g("Óbito só no leve"), g("Óbito só no pesado"), g("Óbito nos dois")
    razao = (leve + dois) / max(pesado + dois, 1)
    como_ler(f"Em {n(base)} colisões entre um veículo leve e um pesado com desfecho registrado "
             f"dos dois lados, houve óbito no leve em {n(leve + dois)} ({p(100*(leve+dois)/base, 2)}) "
             f"e no pesado em {n(pesado + dois)} ({p(100*(pesado+dois)/base, 2)}). "
             f"**Para cada colisão com morte no pesado, há {str(round(razao)).replace('.', ',')} "
             f"com morte no leve.** Nas demais {n(g('Nenhum óbito'))} ninguém morreu.")
    cuidado(f"{n(sem)} colisões ficaram fora do percentual porque um dos veículos não tem "
            "ocupante com desfecho registrado. 'Leve' reúne automóvel, caminhonete, "
            "camioneta e utilitário; 'pesado', caminhão, caminhão-trator e chassi-plataforma.")


def q2(consultar):
    titulo(2, "Em qual combinação de veículos a proporção de óbito no veículo é maior?")
    cond, rot = filtro_dois_veiculos("q2_todos")
    gs = ", ".join(f"'{g}'" for g in GRUPOS)
    d = consultar(f"""
        SELECT grupo_veiculo AS g, grupo_veiculo_cp AS gc, count(*) AS n,
               100.0 * avg((severidade_veiculo = 'obito')::int) AS pct
        FROM fato_par_veiculo
        WHERE contraparte_tipo = 'veiculo' {cond}
          AND severidade_veiculo <> 'sem_ocupante_com_desfecho'
          AND grupo_veiculo IN ({gs}) AND grupo_veiculo_cp IN ({gs})
        GROUP BY 1, 2""")
    legenda("2013–2025", f"colisões entre veículos, {rot}", f"{n(d.n.sum())} colisões")
    ordem = list(GRUPOS)
    m = d.pivot(index="g", columns="gc", values="pct").reindex(index=ordem, columns=ordem)
    nn = d.pivot(index="g", columns="gc", values="n").reindex(index=ordem, columns=ordem)
    txt = m.copy().astype(object)
    for i in ordem:
        for j in ordem:
            v, c = m.loc[i, j], nn.loc[i, j]
            txt.loc[i, j] = "" if pd.isna(v) else (p(v) + ("*" if c < 500 else ""))
    fig = go.Figure(go.Heatmap(
        z=m.values, x=[GRUPOS[c] for c in ordem], y=[GRUPOS[r] for r in ordem],
        text=txt.values, texttemplate="%{text}", colorscale="Reds",
        customdata=nn.values, hovertemplate="%{y} contra %{x}<br>%{z:.2f}% com óbito"
                                             "<br>%{customdata:,} colisões<extra></extra>",
        colorbar=dict(title="% com óbito")))
    fig.update_xaxes(title="contra (contraparte)", side="top")
    fig.update_yaxes(title="veículo onde se mede o óbito", autorange="reversed")
    grafico(fig, 470)
    t = d.sort_values("pct", ascending=False)
    top, low = t.iloc[0], t[t.n >= 500].iloc[-1]
    como_ler(f"Cada linha é o veículo em que se mede o óbito; cada coluna, contra quem ele "
             f"colidiu. A maior proporção é **{GRUPOS[top.g].lower()} contra "
             f"{GRUPOS[top.gc].lower()}: {p(top.pct)}** das colisões com óbito "
             f"{NO_GRUPO[top.g]}. A menor (entre células com 500+ colisões) é "
             f"{GRUPOS[low.g].lower()} contra {GRUPOS[low.gc].lower()}: {p(low.pct, 2)}. "
             "A diagonal mostra colisões entre veículos do mesmo grupo.")
    cuidado("Proporção de colisões com pelo menos um ocupante morto no veículo da linha, "
            "entre veículos com desfecho registrado. * = menos de 500 colisões na célula. "
            "Mostra envolvimento e desfecho, não risco por quilômetro rodado.")


def q3(consultar):
    d = consultar("""
        SELECT v.tipo_veiculo AS tipo, p.desfecho, count(*) AS pessoas
        FROM fato_pessoa p
        JOIN fato_veiculo v ON v.ano_sinistro = p.ano_sinistro
                           AND CAST(v.id_veiculo AS VARCHAR) = CAST(p.id_veiculo AS VARCHAR)
        WHERE p.papel = 'ocupante' AND v.tipo_veiculo IN ('Motocicleta', 'Automóvel')
        GROUP BY 1, 2""")
    d["desfecho"] = d.desfecho.map(DESFECHO)
    d["pct"] = 100 * d.pessoas / d.groupby("tipo").pessoas.transform("sum")
    cabecalho(3, "Como se comparam os desfechos dos ocupantes de motocicletas e de automóveis?",
              "2013–2025", "ocupantes (condutores e passageiros)", f"{n(d.pessoas.sum())} pessoas")
    fig = px.bar(d, y="tipo", x="pct", color="desfecho", orientation="h",
                 category_orders={"desfecho": list(COR_DESFECHO), "tipo": ["Automóvel", "Motocicleta"]},
                 color_discrete_map=COR_DESFECHO, text=d.pct.map(lambda v: p(v, 0) if v >= 3 else ""),
                 labels={"pct": "% dos ocupantes", "tipo": "", "desfecho": "Desfecho"},
                 hover_data={"pessoas": ":,"})
    grafico(fig, 300)
    inf = d[d.desfecho != "Não informado"].copy()
    inf["pct_inf"] = 100 * inf.pessoas / inf.groupby("tipo").pessoas.transform("sum")
    def v(t, des): return float(inf.loc[(inf.tipo == t) & (inf.desfecho == des), "pct_inf"].sum())
    om, oa = v("Motocicleta", "Óbito"), v("Automóvel", "Óbito")
    im, ia = v("Motocicleta", "Ileso"), v("Automóvel", "Ileso")
    gm = v("Motocicleta", "Lesões graves") + om
    ga = v("Automóvel", "Lesões graves") + oa
    como_ler(f"Entre ocupantes com desfecho informado, **{p(om)} dos que estavam numa "
             f"motocicleta morreram, contra {p(oa)} dos que estavam num automóvel** — "
             f"{str(round(om/oa, 1)).replace('.', ',')} vezes mais. Lesão grave ou morte: "
             f"{p(gm)} na moto, {p(ga)} no automóvel. Saíram ilesos {p(im)} dos ocupantes de "
             f"moto e {p(ia)} dos de automóvel.")
    a = consultar(f"""
        SELECT p.ano_sinistro AS ano, v.tipo_veiculo AS tipo,
               100.0 * avg((p.desfecho = 'obito')::int) AS pct_obito
        FROM fato_pessoa p
        JOIN fato_veiculo v ON v.ano_sinistro = p.ano_sinistro
                           AND CAST(v.id_veiculo AS VARCHAR) = CAST(p.id_veiculo AS VARCHAR)
        WHERE p.papel = 'ocupante' AND p.desfecho <> 'nao_informado'
          AND v.tipo_veiculo IN ('Motocicleta', 'Automóvel')
        GROUP BY 1, 2 ORDER BY 1""")
    fig2 = px.line(a, x="ano", y="pct_obito", color="tipo", markers=True,
                   labels={"pct_obito": "% de óbito entre ocupantes", "ano": "", "tipo": ""},
                   color_discrete_map={"Motocicleta": "#b30000", "Automóvel": "#2b8cbe"})
    st.caption("Proporção de óbito entre ocupantes com desfecho informado, por ano")
    grafico(fig2, 320)
    cuidado("Compara o desfecho de quem estava no veículo, não a segurança do veículo: "
            "motos e automóveis circulam em condições, distâncias e quantidades diferentes, "
            "e a base não tem dado de exposição.")


def q4(consultar):
    titulo(4, "Quais causas apresentam a maior proporção de sinistros com vítimas fatais?")
    nivel = st.radio("Nível da causa", ["Grupo (19)", "Detalhada"], horizontal=True, key="q4_nivel")
    col = "causa_grupo" if nivel.startswith("Grupo") else "causa_detalhada"
    minimo = 0 if col == "causa_grupo" else 300
    d = consultar(f"""
        SELECT {col} AS causa, count(*) AS com_vitimas, count_if({FT}) AS fatais,
               100.0 * avg({FT}::int) AS letal
        FROM fato_sinistro WHERE ano_sinistro >= 2017 AND {CV}
        GROUP BY 1 HAVING count(*) >= {minimo} ORDER BY letal DESC""")
    geral = consultar(f"SELECT 100.0 * avg({FT}::int) AS l FROM fato_sinistro "
                      f"WHERE ano_sinistro >= 2017 AND {CV}").l.iloc[0]
    mostra = d if col == "causa_grupo" else d.head(20)
    legenda("2017–2025", "sinistros com vítimas" + ("" if minimo == 0 else
              f"; causas com {minimo}+ casos, 20 mais letais"), f"{n(d.com_vitimas.sum())} sinistros")
    fig = px.bar(mostra.iloc[::-1], x="letal", y="causa", orientation="h",
                 text=mostra.iloc[::-1].apply(lambda r: f"{p(r.letal)}  ({n(r.com_vitimas)})", axis=1),
                 labels={"letal": "% com morte", "causa": ""}, color="letal",
                 color_continuous_scale="Reds")
    fig.add_vline(x=geral, line_dash="dot", line_color="#636363", layer="below",
                  annotation_text=f"média {p(geral)}", annotation_position="bottom right")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, mostra.letal.max() * 1.35])
    fig.update_layout(coloraxis_showscale=False)
    grafico(fig, 30 * len(mostra) + 120)
    freq = d.sort_values("com_vitimas", ascending=False).iloc[0]
    como_ler(f"A barra é a proporção de sinistros com morte entre os sinistros com vítimas de "
             f"cada causa; entre parênteses, quantos sinistros a causa teve. A mais letal é "
             f"**{mostra.iloc[0].causa}: {p(mostra.iloc[0].letal)}**, contra a média de {p(geral)}. "
             f"A mais frequente, {freq.causa} ({n(freq.com_vitimas)} sinistros), tem letalidade de "
             f"{p(freq.letal)} — causa frequente e causa mortal não são a mesma coisa.")
    cuidado("A causa é atribuída ao sinistro pelo boletim, não a um veículo ou pessoa. "
            "Janela a partir de 2017: antes disso, 28% dos sinistros têm causa 'Não especificada'.")


def q5(consultar):
    d = consultar(f"""
        SELECT fase_dia, count(*) AS com_vitimas, count_if({FT}) AS fatais,
               100.0 * avg({FT}::int) AS letal
        FROM fato_sinistro WHERE {CV} AND fase_dia <> 'Não Informado' GROUP BY 1""")
    ordem = ["Amanhecer", "Pleno dia", "Anoitecer", "Plena Noite"]
    d["fase_dia"] = pd.Categorical(d.fase_dia, ordem, ordered=True)
    d = d.sort_values("fase_dia")
    d["part_cv"] = 100 * d.com_vitimas / d.com_vitimas.sum()
    d["part_ft"] = 100 * d.fatais / d.fatais.sum()
    cabecalho(5, "Qual período do dia concentra a maior proporção de sinistros fatais?",
              "2008–2025", "sinistros com vítimas", f"{n(d.com_vitimas.sum())} sinistros")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Proporção de sinistros com morte, em cada período")
        fig = px.bar(d, x="fase_dia", y="letal", text=d.letal.map(p),
                     labels={"fase_dia": "", "letal": "% com morte"},
                     color="letal", color_continuous_scale="Reds",
                     range_color=[0, d.letal.max()])
        fig.update_layout(coloraxis_showscale=False)
        grafico(fig, 360)
    with c2:
        st.caption("Peso de cada período: nos sinistros com vítimas × nos sinistros fatais")
        m = d.melt(id_vars="fase_dia", value_vars=["part_cv", "part_ft"], var_name="serie",
                   value_name="pct")
        m["serie"] = m.serie.map({"part_cv": "sinistros com vítimas", "part_ft": "sinistros fatais"})
        fig2 = px.bar(m, x="fase_dia", y="pct", color="serie", barmode="group",
                      text=m.pct.map(lambda v: p(v, 0)),
                      color_discrete_map={"sinistros com vítimas": "#9ecae1",
                                          "sinistros fatais": "#b30000"},
                      labels={"fase_dia": "", "pct": "% do total", "serie": ""})
        fig2.update_traces(textangle=0, textposition="outside", cliponaxis=False)
        fig2.update_layout(legend=dict(orientation="h", y=1.12, x=0))
        grafico(fig2, 360)
    noite = d[d.fase_dia == "Plena Noite"].iloc[0]
    dia = d[d.fase_dia == "Pleno dia"].iloc[0]
    top = d.sort_values("letal", ascending=False).iloc[0]
    como_ler(f"A maior proporção de mortes está no **{str(top.fase_dia).lower()} "
             f"({p(top.letal)})**. A noite tem {p(noite.part_cv, 0)} dos sinistros com vítimas, "
             f"mas {p(noite.part_ft, 0)} dos fatais; o pleno dia tem {p(dia.part_cv, 0)} dos "
             f"sinistros com vítimas e {p(dia.part_ft, 0)} dos fatais. Um sinistro com vítimas à "
             f"noite é fatal em {p(noite.letal)} dos casos; durante o dia, em {p(dia.letal)} — "
             f"{str(round(noite.letal/dia.letal, 1)).replace('.', ',')} vezes mais.")
    cuidado("Período do dia conforme o boletim. Não separa o efeito da escuridão do efeito de outros "
            "fatores que mudam à noite, como velocidade, álcool, sono e tipo de tráfego.")


def q6(consultar):
    d = consultar(f"""
        SELECT hour(horario) AS hora, dia_semana AS dia, count(*) AS com_vitimas,
               count_if({FT}) AS fatais, 100.0 * avg({FT}::int) AS letal
        FROM fato_sinistro WHERE {CV} GROUP BY 1, 2""")
    cabecalho(6, "Como é o mapa hora × dia da semana dos sinistros com morte?",
              "2008–2025", "sinistros com vítimas", f"{n(d.com_vitimas.sum())} sinistros, "
              f"{n(d.fatais.sum())} fatais")
    def mapa(col, titulo, escala, fmt):
        m = d.pivot(index="dia", columns="hora", values=col).reindex(DIAS)
        fig = go.Figure(go.Heatmap(z=m.values, x=[f"{h}h" for h in m.columns], y=m.index,
                                   colorscale=escala, colorbar=dict(title=titulo),
                                   hovertemplate="%{y}, %{x}<br>" + fmt + "<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        grafico(fig, 360)
    st.caption("Quantos sinistros fatais acontecem em cada hora de cada dia (soma de 18 anos)")
    mapa("fatais", "fatais", "Reds", "%{z:,} sinistros fatais")
    st.caption("Proporção de sinistros com morte entre os sinistros com vítimas, em cada célula")
    mapa("letal", "% com morte", "Purples", "%{z:.1f}% com morte")
    top_n = d.sort_values("fatais", ascending=False).iloc[0]
    top_l = d.sort_values("letal", ascending=False).iloc[0]
    madrug = d[d.hora.between(0, 5)]
    tarde = d[d.hora.between(12, 17)]
    lm = 100 * madrug.fatais.sum() / madrug.com_vitimas.sum()
    lt = 100 * tarde.fatais.sum() / tarde.com_vitimas.sum()
    como_ler(f"O primeiro mapa mostra **quando há mais mortes**: o pico é {top_n.dia.lower()} às "
             f"{int(top_n.hora)}h ({n(top_n.fatais)} sinistros fatais em 18 anos). O segundo "
             f"mostra **quando um sinistro tem mais chance de matar**: {top_l.dia.lower()} às "
             f"{int(top_l.hora)}h ({p(top_l.letal)}). Os dois mapas não coincidem: da meia-noite "
             f"às 5h, {p(lm)} dos sinistros com vítimas são fatais; das 12h às 17h, {p(lt)}.")
    cuidado("Hora conforme registrada no boletim. As madrugadas têm menos sinistros, então a "
            "proporção de cada célula se apoia em menos casos; passe o mouse para ver o número.")


def q7(consultar):
    d = consultar(f"""
        SELECT tipo_pista,
               count(*) AS com_vitimas,
               count_if(tipo_detalhado = 'Colisão frontal') AS frontais,
               100.0 * avg((tipo_detalhado = 'Colisão frontal')::int) AS pct_frontal,
               100.0 * avg(CASE WHEN tipo_detalhado = 'Colisão frontal' THEN {FT}::int END) AS letal_frontal,
               100.0 * avg(CASE WHEN tipo_detalhado <> 'Colisão frontal' THEN {FT}::int END) AS letal_demais
        FROM fato_sinistro WHERE {CV} AND tipo_pista IN ('Simples', 'Dupla', 'Múltipla')
        GROUP BY 1""")
    ordem = ["Simples", "Dupla", "Múltipla"]
    d["tipo_pista"] = pd.Categorical(d.tipo_pista, ordem, ordered=True)
    d = d.sort_values("tipo_pista")
    cabecalho(7, "Como a proporção de colisões frontais e sua letalidade diferem entre pista "
                 "simples, dupla e múltipla?", "2008–2025", "sinistros com vítimas",
              f"{n(d.com_vitimas.sum())} sinistros, {n(d.frontais.sum())} colisões frontais")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Quanto dos sinistros com vítimas é colisão frontal")
        fig = px.bar(d, x="tipo_pista", y="pct_frontal", text=d.pct_frontal.map(p),
                     labels={"tipo_pista": "pista", "pct_frontal": "% colisões frontais"},
                     color_discrete_sequence=["#6a51a3"])
        grafico(fig, 360)
    with c2:
        st.caption("Proporção com morte: colisão frontal × demais tipos")
        m = d.melt(id_vars="tipo_pista", value_vars=["letal_frontal", "letal_demais"],
                   var_name="tipo", value_name="pct")
        m["tipo"] = m.tipo.map({"letal_frontal": "colisão frontal", "letal_demais": "demais tipos"})
        fig2 = px.bar(m, x="tipo_pista", y="pct", color="tipo", barmode="group",
                      text=m.pct.map(p), labels={"tipo_pista": "pista", "pct": "% com morte", "tipo": ""},
                      color_discrete_map={"colisão frontal": "#b30000", "demais tipos": "#9ecae1"})
        fig2.update_traces(textangle=0, textposition="outside", cliponaxis=False)
        fig2.update_layout(legend=dict(orientation="h", y=1.12, x=0))
        grafico(fig2, 360)
    s, du = d[d.tipo_pista == "Simples"].iloc[0], d[d.tipo_pista == "Dupla"].iloc[0]
    como_ler(f"Em pista simples, **{p(s.pct_frontal)} dos sinistros com vítimas são colisões "
             f"frontais; em pista dupla, {p(du.pct_frontal)}**. Quando a frontal acontece, é fatal "
             f"em {p(s.letal_frontal)} dos casos na pista simples e {p(du.letal_frontal)} na dupla — "
             f"em qualquer pista, bem acima dos demais tipos ({p(s.letal_demais)} e "
             f"{p(du.letal_demais)}).")
    cuidado("Comparação descritiva entre trechos diferentes, não o efeito de duplicar uma "
            "estrada: pistas simples e duplas diferem também em tráfego, relevo, velocidade e "
            "região.")


def q8(consultar):
    titulo(8, "Quais trechos de 5 km aparecem entre os mais graves ano após ano?")
    c1, c2 = st.columns(2)
    metrica = c1.radio("Medida", ["Sinistros com vítimas", "Óbitos"], horizontal=True, key="q8_m")
    topn = c2.select_slider("Tamanho do ranking anual", [50, 100, 200], value=100, key="q8_n")
    col = "count(*)" if metrica.startswith("Sinistros") else "sum(n_mortos)"
    d = consultar(f"""
        WITH base AS (
          SELECT ano_sinistro AS ano, uf, trecho_5km AS trecho, {col} AS valor
          FROM fato_sinistro WHERE {CV} GROUP BY 1, 2, 3),
        rk AS (SELECT *, rank() OVER (PARTITION BY ano ORDER BY valor DESC) AS r FROM base)
        SELECT uf, trecho, count(*) FILTER (WHERE r <= {topn}) AS anos_no_top,
               sum(valor) AS total
        FROM rk GROUP BY 1, 2 HAVING count(*) FILTER (WHERE r <= {topn}) > 0""")
    def rotulo(r):
        br, km = r.trecho.split("_")
        km = int(float(km))
        return f"BR-{int(br):03d} km {km}–{km + 5} ({r.uf})"
    d["trecho_rot"] = d.apply(rotulo, axis=1)
    legenda("2008–2025 (18 anos)", f"{metrica.lower()} por trecho e ano; ranking dos {topn} "
              f"maiores de cada ano", f"{n(len(d))} trechos entraram no ranking ao menos uma vez")
    top = d.sort_values(["anos_no_top", "total"], ascending=False).head(25)
    fig = px.bar(top.iloc[::-1], x="anos_no_top", y="trecho_rot", orientation="h",
                 text=top.iloc[::-1].apply(lambda r: f"{r.anos_no_top} anos · {n(r.total)}", axis=1),
                 labels={"anos_no_top": f"anos entre os {topn} maiores", "trecho_rot": ""},
                 color="anos_no_top", color_continuous_scale="Reds", range_x=[0, 19])
    fig.update_layout(coloraxis_showscale=False)
    grafico(fig, 760)
    dist = d.groupby("anos_no_top").size().reset_index(name="trechos")
    st.caption("Quantos trechos ficaram no ranking por quantos anos")
    fig2 = px.bar(dist, x="anos_no_top", y="trechos", text="trechos",
                  labels={"anos_no_top": f"anos entre os {topn} maiores", "trechos": "trechos"},
                  color_discrete_sequence=["#fc8d59"])
    grafico(fig2, 300)
    sempre = int((d.anos_no_top == 18).sum())
    uma = int((d.anos_no_top == 1).sum())
    como_ler(f"Cada barra é um trecho de 5 km; o comprimento é o número de anos em que ele "
             f"esteve entre os {topn} com mais {metrica.lower()} do país, e o número ao lado é o "
             f"total do período. **{sempre} trechos estiveram no ranking em todos os 18 anos** — "
             f"pontos persistentes, não acaso de um ano. Na outra ponta, {uma} trechos apareceram "
             "uma única vez.")
    cuidado("Volume de sinistros reflete também o volume de tráfego do trecho; sem contagem de "
            "veículos, não é taxa de risco. O trecho é identificado por estado + BR + km, porque "
            "a quilometragem da PRF recomeça em cada estado.")


def q9(consultar):
    d = consultar(f"""
        SELECT br, count(*) AS com_vitimas, sum(n_mortos) AS mortos,
               100.0 * sum(n_mortos) / count(*) AS mortos_100
        FROM fato_sinistro WHERE {CV} GROUP BY 1""")
    geral = 100 * d.mortos.sum() / d.com_vitimas.sum()
    g = d[d.com_vitimas >= 1000].copy()
    g["rot"] = "BR-" + g.br.astype(int).astype(str).str.zfill(3)
    marcar = set(g.nlargest(6, "com_vitimas").rot) | set(g.nlargest(5, "mortos_100").rot)
    g["texto"] = g.rot.where(g.rot.isin(marcar), "")
    cabecalho(9, "Em cada BR, como se comparam volume de sinistros e letalidade?",
              "2008–2025", f"sinistros com vítimas; BRs com 1.000+ casos ({len(g)} de {len(d)})",
              f"{n(g.com_vitimas.sum())} sinistros")
    fig = px.scatter(g, x="com_vitimas", y="mortos_100", text="texto", log_x=True,
                     size="mortos", size_max=40, hover_name="rot",
                     hover_data={"texto": False, "com_vitimas": ":,", "mortos": ":,",
                                 "mortos_100": ":.1f"},
                     labels={"com_vitimas": "sinistros com vítimas (escala log)",
                             "mortos_100": "mortos por 100 sinistros com vítimas"},
                     color="mortos_100", color_continuous_scale="Reds")
    fig.add_hline(y=geral, line_dash="dot", line_color="#636363", layer="below",
                  annotation_text=f"média {str(round(geral, 1)).replace('.', ',')}",
                  annotation_position="top left")
    fig.update_traces(textposition="top center")
    marcas = [1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]
    fig.update_xaxes(tickvals=marcas, ticktext=[n(v) for v in marcas], minor=dict(showgrid=False))
    fig.update_layout(coloraxis_showscale=False)
    grafico(fig, 560)
    vol = g.nlargest(1, "com_vitimas").iloc[0]
    let = g.nlargest(1, "mortos_100").iloc[0]
    como_ler(f"Cada bolha é uma BR; quanto mais à direita, mais sinistros; quanto mais alta, "
             f"mais mortos por sinistro; o tamanho é o total de mortos. A de maior volume é a "
             f"**{vol.rot}** ({n(vol.com_vitimas)} sinistros, "
             f"{str(round(vol.mortos_100, 1)).replace('.', ',')} mortos por 100). A mais letal é a "
             f"**{let.rot}** ({str(round(let.mortos_100, 1)).replace('.', ',')} mortos por 100, "
             f"em {n(let.com_vitimas)} sinistros). A linha pontilhada é a média nacional, "
             f"{str(round(geral, 1)).replace('.', ',')}.")
    cuidado("Sem dado de tráfego, não é risco por quilômetro: uma BR movimentada tem mais "
            "sinistros por ter mais veículos. A letalidade compara a gravidade quando o "
            "sinistro acontece, não a chance de ele acontecer.")


def q10(consultar):
    causas = ["Álcool", "Sono", "Velocidade"]
    lista = ", ".join(f"'{c}'" for c in causas)
    h = consultar(f"""
        SELECT causa_grupo AS causa, hour(horario) AS hora, count(*) AS n
        FROM fato_sinistro WHERE ano_sinistro >= 2017 AND {CV} AND causa_grupo IN ({lista})
        GROUP BY 1, 2
        UNION ALL
        SELECT 'Todas as causas', hour(horario), count(*)
        FROM fato_sinistro WHERE ano_sinistro >= 2017 AND {CV} GROUP BY 2""")
    h["pct"] = 100 * h.n / h.groupby("causa").n.transform("sum")
    w = consultar(f"""
        SELECT causa_grupo AS causa, dia_semana AS dia, count(*) AS n
        FROM fato_sinistro WHERE ano_sinistro >= 2017 AND {CV} AND causa_grupo IN ({lista})
        GROUP BY 1, 2
        UNION ALL
        SELECT 'Todas as causas', dia_semana, count(*)
        FROM fato_sinistro WHERE ano_sinistro >= 2017 AND {CV} GROUP BY 2""")
    w["pct"] = 100 * w.n / w.groupby("causa").n.transform("sum")
    tot = h[h.causa != "Todas as causas"].groupby("causa").n.sum()
    cabecalho(10, "Em que horas e dias da semana se concentram os sinistros por álcool, sono e velocidade?",
              "2017–2025", "sinistros com vítimas de cada causa",
              " · ".join(f"{c}: {n(tot[c])}" for c in causas))
    cores = {"Álcool": "#6a51a3", "Sono": "#2b8cbe", "Velocidade": "#e6550d", "Todas as causas": "#969696"}
    st.caption("Distribuição de cada causa pelas horas do dia (cada linha soma 100%)")
    ordem_c = {"causa": causas + ["Todas as causas"]}
    fig = px.line(h.sort_values("hora"), x="hora", y="pct", color="causa", markers=True,
                  category_orders=ordem_c, color_discrete_map=cores, labels={"hora": "hora do dia", "pct": "% dos sinistros da causa", "causa": ""})
    fig.for_each_trace(lambda t: t.update(line=dict(dash="dot")) if t.name == "Todas as causas" else None)
    fig.update_xaxes(dtick=2)
    grafico(fig, 400)
    st.caption("Distribuição de cada causa pelos dias da semana (cada cor soma 100%)")
    w["dia"] = pd.Categorical(w.dia, DIAS, ordered=True)
    fig2 = px.bar(w.sort_values("dia"), x="dia", y="pct", color="causa", barmode="group",
                  category_orders=ordem_c, color_discrete_map=cores, labels={"dia": "", "pct": "% dos sinistros da causa", "causa": ""})
    grafico(fig2, 380)
    pico = {c: int(h[h.causa == c].sort_values("pct").iloc[-1].hora) for c in causas}
    fds = {c: float(w[(w.causa == c) & (w.dia.isin(["Sábado", "Domingo"]))].pct.sum())
           for c in causas + ["Todas as causas"]}
    como_ler(f"Cada causa tem seu próprio horário: **sono às {pico['Sono']}h, velocidade às "
             f"{pico['Velocidade']}h e álcool às {pico['Álcool']}h** (hora com maior parcela de "
             f"cada uma). Sábado e domingo concentram {p(fds['Álcool'], 0)} dos sinistros por "
             f"álcool, contra {p(fds['Todas as causas'], 0)} do conjunto de todas as causas; "
             f"para sono, {p(fds['Sono'], 0)}; para velocidade, {p(fds['Velocidade'], 0)}. "
             "A linha pontilhada é a referência de todas as causas.")
    cuidado("A causa é a atribuída ao sinistro no boletim. Comparar distribuições (cada causa "
            "soma 100%) mostra quando cada uma acontece, independentemente de quantas são.")


PERGUNTAS = [("1 · Leve × pesado", q1), ("2 · Matriz de colisões", q2),
             ("3 · Moto × automóvel", q3), ("4 · Causas letais", q4),
             ("5 · Período do dia", q5), ("6 · Hora × dia", q6),
             ("7 · Frontais por pista", q7), ("8 · Trechos persistentes", q8),
             ("9 · BRs: volume × letalidade", q9), ("10 · Álcool, sono, velocidade", q10)]


def tela_perguntas(consultar):
    estilo.cabecalho("Perguntas",
                     "Respostas prontas a dez perguntas sobre colisões, causas, horários e trechos, calculadas "
                     "sobre a mesma base da Consulta livre. Cada aba traz o critério usado e como ler o gráfico. "
                     "Estes números são de exploração e não vão para o texto do TCC.",
                     "Exploração · perguntas selecionadas")
    with st.expander("Critérios usados em todas as perguntas"):
        st.markdown(
            "- **Com vítimas** = sinistros classificados pela PRF como com feridos ou com mortos. "
            "Toda proporção de mortes usa essa base, porque a saída dos sinistros sem vítimas do "
            "registro em 2015 e 2018 distorceria qualquer proporção calculada sobre o total.\n"
            "- **Colisões (perguntas 1 e 2)**: por padrão, só sinistros com exatamente dois "
            "veículos — aí o par é a colisão. Há uma opção para incluir os demais.\n"
            "- **Óbito no veículo**: só entre veículos com desfecho registrado.\n"
            "- **Causa**: a partir de 2017, quando deixa de existir causa não especificada.\n"
            "- Tudo é **envolvimento**, nunca risco: a base não tem dado de exposição (frota, "
            "quilômetros rodados, tráfego).")
    abas = st.tabs([rot for rot, _ in PERGUNTAS])
    for aba, (_, f) in zip(abas, PERGUNTAS):
        with aba:
            f(consultar)
