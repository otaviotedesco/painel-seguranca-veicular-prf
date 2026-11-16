import pathlib
import duckdb, pandas as pd, streamlit as st, plotly.express as px
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from recorte_tcc import SQL as RECORTE_TCC

BANCO = pathlib.Path(__file__).resolve().parents[3] / "03_dados" / "09_painel" / "painel.duckdb"
QUEBRAS = {2015: "e-DAT: sinistros sem vítimas passam a poder ser declarados pela internet, fora do registro presencial",
           2018: "Mudança de procedimento: segundo degrau no registro de sinistros sem vítimas",
           2021: "Terceiro vocabulário de causa do acidente"}

st.set_page_config(page_title="Segurança veicular nas rodovias federais — painel do TCC", layout="wide",
                   initial_sidebar_state="expanded")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import estilo
estilo.aplicar()

TABELAS = ["fato_sinistro", "fato_veiculo", "fato_pessoa", "fato_par_veiculo"]
PARQUET = BANCO.parent

def fonte_disponivel():
    return BANCO.exists() or all((PARQUET / f"{t}.parquet").exists() for t in TABELAS)

def caminho_banco():
    if BANCO.exists():
        return BANCO
    import tempfile, os
    destino = pathlib.Path(tempfile.gettempdir()) / "painel_tcc" / "painel.duckdb"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        provisorio = destino.with_name(f"montando_{os.getpid()}.duckdb")
        provisorio.unlink(missing_ok=True)
        con = duckdb.connect(str(provisorio))
        for t in TABELAS:
            con.execute(f"CREATE TABLE {t} AS SELECT * FROM read_parquet('{(PARQUET / (t + '.parquet')).as_posix()}')")
        con.execute("CHECKPOINT"); con.close()
        os.replace(provisorio, destino)
    return destino

@st.cache_resource(show_spinner="Preparando os dados (só na primeira abertura)...")
def conectar():
    return duckdb.connect(str(caminho_banco()), read_only=True)

@st.cache_data(show_spinner=False)
def consultar(sql: str) -> pd.DataFrame:
    return conectar().execute(sql).fetch_df()

BASES = {
    "Sinistros": "fato_sinistro s",
    "Veiculos":  "fato_veiculo v JOIN fato_sinistro s USING (ano_sinistro, id)",
    "Pessoas":   "fato_pessoa p JOIN fato_sinistro s USING (ano_sinistro, id) "
                 "LEFT JOIN fato_veiculo v ON p.ano_sinistro = v.ano_sinistro "
                 "AND p.id_veiculo = v.id_veiculo",
    "Pares":     "fato_par_veiculo r JOIN fato_sinistro s USING (ano_sinistro, id)",
}
MEDIDAS = {
    "Sinistros": "count(DISTINCT (s.ano_sinistro || '-' || s.id)) AS sinistros, sum(s.n_mortos) AS mortos, "
                 "sum(s.n_feridos) AS feridos, sum(s.n_pessoas) AS pessoas_envolvidas, "
                 "sum(s.n_veiculos) AS veiculos_envolvidos",
    "Veiculos":  "count(DISTINCT (v.ano_sinistro || '-' || v.id_veiculo)) AS veiculos, count(DISTINCT (s.ano_sinistro || '-' || s.id)) AS sinistros, "
                 "sum(CASE WHEN v.severidade_veiculo = 'obito' THEN 1 ELSE 0 END) AS veiculos_com_obito",
    "Pessoas":   "count(DISTINCT (p.ano_sinistro || '-' || p.pesid)) AS pessoas, "
                 "sum(CASE WHEN p.desfecho='obito' THEN 1 ELSE 0 END) AS obitos, "
                 "sum(CASE WHEN p.desfecho='lesoes_graves' THEN 1 ELSE 0 END) AS lesoes_graves, "
                 "sum(CASE WHEN p.desfecho='lesoes_leves' THEN 1 ELSE 0 END) AS lesoes_leves, "
                 "sum(CASE WHEN p.desfecho='ileso' THEN 1 ELSE 0 END) AS ilesos, "
                 "round(avg(p.idade_num), 1) AS idade_media, "
                 "count(p.idade_num) AS base_idade",
    "Pares":     "count(*) AS pares, count(DISTINCT (s.ano_sinistro || '-' || s.id)) AS sinistros, "
                 "sum(CASE WHEN r.severidade_veiculo='obito' THEN 1 ELSE 0 END) AS obito_no_veiculo, "
                 "sum(CASE WHEN r.severidade_veiculo_cp='obito' THEN 1 ELSE 0 END) AS obito_na_contraparte",
}
PRINCIPAL = {"Sinistros": "count(DISTINCT (s.ano_sinistro || '-' || s.id))",
             "Veiculos":  "count(DISTINCT (v.ano_sinistro || '-' || v.id_veiculo))",
             "Pessoas":   "count(DISTINCT (p.ano_sinistro || '-' || p.pesid))",
             "Pares":     "count(*)"}
NOME_PRINCIPAL = {"Sinistros": "sinistros", "Veiculos": "veiculos",
                  "Pessoas": "pessoas", "Pares": "pares"}

DIMENSOES = {
    "Nenhuma (serie total)":   (None, None),
    "Unidade federativa":      ("s.uf", None),
    "Fase do dia":             ("s.fase_dia", None),
    "Condicao meteorologica":  ("s.condicao_metereologica", None),
    "Tipo de pista":           ("s.tipo_pista", None),
    "Classificacao":           ("s.classificacao_acidente", None),
    "Tipo de acidente":        ("s.tipo_detalhado", None),
    "Tipo de acidente (grupo)": ("s.tipo_categoria", None),
    "Causa":                   ("s.causa_detalhada", None),
    "Causa (grupo)":           ("s.causa_grupo", None),
    "Causa (origem)":          ("s.causa_origem", None),
    "Dia da semana":           ("s.dia_semana", None),
    "Uso do solo":             ("s.uso_solo_norm", None),
    "Grupo de veiculo":        ("v.grupo_veiculo", {"Veiculos", "Pessoas"}),
    "Faixa de ano de fabric.": ("v.faixa_ano_fab", {"Veiculos", "Pessoas"}),
    "Fabricante":              ("v.fabricante", {"Veiculos"}),
    "Familia de modelo":       ("v.familia", {"Veiculos"}),
    "Geracao do modelo":       ("v.geracao_rotulo", {"Veiculos", "Pessoas"}),
    "Papel da pessoa":         ("p.papel", {"Pessoas"}),
    "Sexo":                    ("p.sexo_norm", {"Pessoas"}),
    "Faixa etaria":            ("p.faixa_etaria", {"Pessoas"}),
    "Desfecho":                ("p.desfecho", {"Pessoas"}),
    "Tipo de contraparte":     ("r.contraparte_tipo", {"Pares"}),
    "Modelo consultado":       ("r.familia", {"Pares"}),
    "Modelo da contraparte":   ("r.familia_cp", {"Pares"}),
    "Geracao do modelo consultado": ("r.geracao_rotulo", {"Pares"}),
    "Geracao da contraparte":  ("r.geracao_rotulo_cp", {"Pares"}),
}
GRAFICOS = ["Barras empilhadas", "Linhas", "Area 100% (composicao)", "Mapa de calor"]

NOMES = {
    "condutor_conduta":  "Conduta do condutor",
    "condutor_estado":   "Estado do condutor (alcool, sono)",
    "saude_ou_intencao": "Saude ou intencao",
    "veiculo":           "Falha do veiculo",
    "via":               "Defeito ou tracado da via",
    "superficie_via":    "Superficie da via (escorregadia, oleo)",
    "ambiente":          "Ambiente (clima, animais)",
    "pedestre_ciclista": "Conduta de pedestre ou ciclista",
    "externo":           "Fator externo (agressao, assalto)",
    "outros":            "Outras ou nao especificada",
    "nao_informado":     "Nao informado",
    "colisao":           "Colisao",
    "saida_tombamento":  "Saida de pista ou tombamento",
    "atropelamento":     "Atropelamento",
    "incendio":          "Incendio",
    "evento_pessoal":    "Evento pessoal de transito",
    "leve": "Veiculo leve", "moto": "Motocicleta", "pesado": "Caminhao",
    "onibus": "Onibus", "bicicleta": "Bicicleta", "outro": "Outro veiculo",
    "ocupante": "Ocupante", "pedestre": "Pedestre", "testemunha": "Testemunha",
    "cavaleiro": "Cavaleiro", "sem_pessoa": "Sem pessoa identificada",
    "masculino": "Masculino", "feminino": "Feminino",
    "ileso": "Ileso", "lesoes_leves": "Lesoes leves",
    "lesoes_graves": "Lesoes graves", "obito": "Obito",
    "nenhuma": "Sem contraparte", "animal": "Animal", "objeto_fixo": "Objeto fixo",
    "ambigua": "Contraparte nao atribuivel", "urbano": "Urbano", "rural": "Rural",
    "nao_informada": "Nao informada", "(null)": "Nao informado", "": "Nao informado",
    "NAO_IDENTIFICADO": "Modelo nao identificado",
    "INDETERMINADO": "Modelo nao identificado",
    "sem_desfecho_conhecido": "Sem desfecho conhecido",
    "sem_ocupante_com_desfecho": "Sem ocupante com desfecho",
}
legivel = lambda v: NOMES.get(str(v), str(v))

lit = lambda vs: ", ".join("'" + str(v).replace("'", "''") + "'" for v in vs)

def montar_filtros(visao):
    f = {}
    st.sidebar.header("Filtros")
    st.sidebar.subheader("Período e local")
    a0, a1 = st.sidebar.slider("Periodo", 2008, 2025, (2008, 2025))
    if (a0, a1) != (2008, 2025):
        f["Periodo"] = f"s.ano_sinistro BETWEEN {a0} AND {a1}"

    ufs = consultar("SELECT DISTINCT uf FROM fato_sinistro WHERE uf <> '' ORDER BY 1").uf.tolist()
    if sel := st.sidebar.multiselect("UF", ufs):
        f["UF"] = f"s.uf IN ({lit(sel)})"
    st.sidebar.subheader("Sinistro")
    caixa = st.sidebar.expander("Condições, tipo e causa", expanded=False)
    for rotulo, col in [("Fase do dia", "fase_dia"), ("Condicao meteorologica", "condicao_metereologica"),
                        ("Tipo de pista", "tipo_pista"), ("Classificacao", "classificacao_acidente"),
                        ("Tipo de acidente", "tipo_detalhado"),
                        ("Tipo de acidente (grupo)", "tipo_categoria"),
                        ("Causa", "causa_detalhada"),
                        ("Causa (grupo)", "causa_grupo"),
                        ("Causa (origem)", "causa_origem")]:
        ops = consultar(f"SELECT DISTINCT {col} AS x FROM fato_sinistro WHERE {col} <> '' ORDER BY 1").x.tolist()
        if sel := caixa.multiselect(rotulo, ops):
            f[rotulo] = f"s.{col} IN ({lit(sel)})"

    if visao in ("Veiculos", "Pessoas", "Pares"):
        pref = "r" if visao == "Pares" else "v"
        st.sidebar.subheader("Veiculo")
        busca = st.sidebar.text_input("Buscar modelo", placeholder="ex.: GOL, ONIX, NIVUS")
        fab = consultar("""SELECT fabricante AS x FROM fato_veiculo
                           GROUP BY 1 ORDER BY count(*) DESC""").x.tolist()
        selfab = st.sidebar.multiselect("Fabricante", fab)
        cond = ["1=1"]
        if busca: cond.append(f"familia ILIKE '%{busca.replace(chr(39), '')}%'")
        if selfab: cond.append(f"fabricante IN ({lit(selfab)})")
        fams = consultar(f"""SELECT fabricante AS fb, familia AS x, count(*) AS n FROM fato_veiculo
                             WHERE {' AND '.join(cond)} GROUP BY 1,2 ORDER BY n DESC LIMIT 300""")
        rot = {f"{r.x} — {r.fb}  ({r.n:,})".replace(",", "."): f"{r.fb}|{r.x}"
               for r in fams.itertuples()}
        if sel := st.sidebar.multiselect("Modelo (familia — fabricante)", list(rot)):
            f["Modelo"] = (f"({pref}.fabricante || '|' || {pref}.familia) "
                           f"IN ({lit([rot[s] for s in sel])})")
        elif selfab:
            f["Fabricante"] = f"{pref}.fabricante IN ({lit(selfab)})"
        cg = [f"geracao_via <> 'fora_catalogo'"]
        if "Modelo" in f:
            cg.append(f"(fabricante || '|' || familia) IN ({lit([rot[s] for s in sel])})")
        elif selfab:
            cg.append(f"fabricante IN ({lit(selfab)})")
        if busca: cg.append(f"familia ILIKE '%{busca.replace(chr(39), '')}%'")
        gers = consultar(f"""SELECT geracao_rotulo AS x, count(*) AS n FROM fato_veiculo
                             WHERE {' AND '.join(cg)} GROUP BY 1 ORDER BY n DESC LIMIT 200""")
        if sel_g := st.sidebar.multiselect("Geracao do modelo", gers.x.tolist(),
                help="Geracao identificada pela mesma regra da analise do TCC: ano de fabricacao e, "
                     "quando ele cabe em duas geracoes, o texto do modelo. Disponivel para as 63 "
                     "familias da tabela de geracoes; 'geracao ambigua' = ano compativel com duas."):
            f["Geracao"] = f"{pref}.geracao_rotulo IN ({lit(sel_g)})"
        faixas = ["<2000", "2000-2009", "2010-2014", "2015-2019", "2020+", "nao_informado"]
        if sel := st.sidebar.multiselect("Faixa de ano de fabricacao", faixas):
            f["Faixa de ano"] = f"{pref}.faixa_ano_fab IN ({lit(sel)})"

    if visao == "Pares":
        st.sidebar.subheader("Contraparte")
        tipos = consultar("SELECT DISTINCT contraparte_tipo AS x FROM fato_par_veiculo ORDER BY 1").x.tolist()
        if sel := st.sidebar.multiselect("Tipo de contraparte", tipos):
            f["Tipo de contraparte"] = f"r.contraparte_tipo IN ({lit(sel)})"
        b2 = st.sidebar.text_input("Buscar modelo da contraparte", placeholder="ex.: JETTA")
        if b2:
            fams2 = consultar(f"""SELECT fabricante AS fb, familia AS x, count(*) AS n FROM fato_veiculo
                                  WHERE familia ILIKE '%{b2.replace(chr(39), '')}%'
                                  GROUP BY 1,2 ORDER BY n DESC LIMIT 100""")
            rot2 = {f"{r.x} — {r.fb}  ({r.n:,})".replace(",", "."): f"{r.fb}|{r.x}"
                    for r in fams2.itertuples()}
            if sel := st.sidebar.multiselect("Modelo da contraparte", list(rot2)):
                f["Modelo da contraparte"] = (f"(r.fabricante_cp || '|' || r.familia_cp) "
                                              f"IN ({lit([rot2[s] for s in sel])})")

    if visao == "Pessoas":
        st.sidebar.subheader("Recorte do TCC")
        if st.sidebar.checkbox("Recorte do TCC", key="recorte_tcc",
                               help="Ocupantes de automovel, 2019-2025, desfecho conhecido, ano de "
                                    "fabricacao valido e modelo identificado — a populacao da analise do TCC"):
            f["Recorte do TCC"] = RECORTE_TCC
        st.sidebar.subheader("Pessoa")
        for rotulo, col, ops in [("Papel", "papel", ["ocupante", "pedestre", "testemunha", "cavaleiro", "outro"]),
                                 ("Sexo", "sexo_norm", ["masculino", "feminino", "nao_informado"]),
                                 ("Faixa etaria", "faixa_etaria", ["0-17", "18-24", "25-39", "40-59", "60+", "nao_informada"]),
                                 ("Desfecho", "desfecho", ["ileso", "lesoes_leves", "lesoes_graves", "obito", "nao_informado"])]:
            if sel := st.sidebar.multiselect(rotulo, ops):
                f[rotulo] = f"p.{col} IN ({lit(sel)})"
    return f

def onde(f, excluir=None):
    cs = [v for k, v in f.items() if k != excluir]
    return " WHERE " + " AND ".join(cs) if cs else ""

def avisos(f, visao, a0=2008, a1=2025):
    av = []
    if a0 <= 2015 <= a1 or a0 <= 2018 <= a1:
        av.append("A queda de registros sem vitimas em 2015 e 2018 e **administrativa** "
                  "(e-DAT e mudanca de procedimento), nao reducao de sinistros. Series de mortos sao comparaveis; totais de sinistros nao.")
    if "Causa (categoria)" in f and a0 <= 2016:
        av.append("O vocabulario de causa mudou em 2017 e 2021. Ate 2016, **28% dos sinistros tinham causa 'Outras'**. "
                  "O nivel detalhado ja unifica as tres geracoes de vocabulario; o rotulo original fica preservado nos dados.")
    if visao in ("Veiculos", "Pares") and a0 <= 2016 <= a1:
        av.append("A identificacao do modelo passa de ~85% para ~94% entre 2016 e 2017. "
                  "Parte de qualquer aumento aparente e melhora de preenchimento, nao mais sinistros.")
    if visao in ("Veiculos", "Pares"):
        av.append("**Nao ha dado de exposicao.** O painel mostra envolvimento, nunca risco: um modelo aparecer mais "
                  "pode significar apenas que ha mais deles circulando.")
    if visao == "Pessoas" and a0 <= 2016 <= a1:
        av.append("A granularidade do registro muda em 2017: a linha deixa de significar 'uma pessoa'. "
                  "As contagens aqui sao sempre por pessoa distinta.")
    if a0 <= 2012:
        av.append("Contagens de 2008 a 2012 vem do DATATRAN publicado, nao recalculadas: nao existe base de pessoas nesses anos.")
    if a0 <= 2015 <= a1:
        av.append("Em 2015 o painel mostra 6.866 mortos, um a menos que o publicado pela PRF: "
                  "uma pessoa foi registrada em duas linhas.")
    return av

def marcar_quebras(fig):
    for ano in QUEBRAS:
        fig.add_vline(x=ano, line_dash="dot", line_color="#b00",
                      annotation_text=str(ano), annotation_position="top")
    return fig

def tela_panorama():
    estilo.cabecalho("Panorama dos sinistros, 2008–2025",
                     "Série histórica dos sinistros e das mortes registrados pela Polícia Rodoviária Federal nas "
                     "rodovias federais, com as mudanças de registro que afetam a leitura de cada curva.",
                     "Exploração · série histórica")
    d = consultar("""SELECT ano_sinistro AS ano, count(DISTINCT id) AS sinistros,
                sum(n_mortos) AS mortos, sum(n_feridos) AS feridos,
                sum(CASE WHEN classificacao_acidente='Sem Vítimas' THEN 1 ELSE 0 END) AS sem_vitimas,
                sum(CASE WHEN classificacao_acidente='Com Vítimas Feridas' THEN 1 ELSE 0 END) AS com_feridas,
                sum(CASE WHEN classificacao_acidente='Com Vítimas Fatais' THEN 1 ELSE 0 END) AS com_fatais
                FROM fato_sinistro GROUP BY 1 ORDER BY 1""")
    estilo.secao("Totais do período")
    c = st.columns(4)
    c[0].metric("Sinistros", f"{d.sinistros.sum():,}".replace(",", "."))
    c[1].metric("Mortos", f"{int(d.mortos.sum()):,}".replace(",", "."))
    c[2].metric("Feridos", f"{int(d.feridos.sum()):,}".replace(",", "."))
    c[3].metric("Anos", f"{d.ano.min()}-{d.ano.max()}")

    estilo.secao("Sinistros por ano",
                 "O total de sinistros mudou de significado em 2015 e 2018. Compare as três vistas para separar "
                 "o que é mudança de registro do que é mudança no trânsito.")
    modo = st.radio("Como exibir a serie",
                    ["Total", "Por classificacao", "Somente com vitimas"], horizontal=True,
                    help="O total nao e comparavel ao longo do tempo: a queda de 2015 e 2018 "
                         "esta inteira na categoria sem vitimas.")

    if modo == "Total":
        st.plotly_chart(marcar_quebras(px.line(d, x="ano", y="sinistros", markers=True,
                        title="Sinistros por ano (total)")), width="stretch")
        st.warning("A queda entre 2014 e 2019 **nao e reducao de sinistros**: e a saida dos "
                   "registros sem vitimas da base. Compare com as outras duas vistas.")
    elif modo == "Por classificacao":
        m = d.melt(id_vars="ano", value_vars=["sem_vitimas", "com_feridas", "com_fatais"],
                   var_name="classificacao", value_name="quantidade")
        m["classificacao"] = m.classificacao.map({"sem_vitimas": "Sem vitimas",
            "com_feridas": "Com vitimas feridas", "com_fatais": "Com vitimas fatais"})
        st.plotly_chart(marcar_quebras(px.line(m, x="ano", y="quantidade", color="classificacao",
                        markers=True, title="Sinistros por ano, separados por classificacao",
                        labels={"quantidade": "sinistros"})), width="stretch")
        f0 = int(d.com_fatais.iloc[0]); f1 = int(d.com_fatais.iloc[-1])
        s0 = int(d.sem_vitimas.iloc[0]); s1 = int(d.sem_vitimas.iloc[-1])
        fe0 = int(d.com_feridas.iloc[0]); fe1 = int(d.com_feridas.iloc[-1])
        st.success(
            "**Como ler.** As tres linhas sao os tres valores do campo de classificacao da PRF e "
            "somam o total de sinistros. A quebra de 2015 e 2018 esta **isolada numa categoria**: "
            f"sem vitimas cai de {s0:,}".replace(",", ".") + f" para {s1:,}".replace(",", ".") +
            f" ({100*(s0-s1)/s0:.0f}% a menos), enquanto com vitimas feridas **sobe** de "
            f"{fe0:,}".replace(",", ".") + f" para {fe1:,}".replace(",", ".") + ". "
            "Se a reducao fosse real, as tres cairiam juntas.\n\n"
            "**O que mais aparece aqui.** Os sinistros com vitimas fatais quase voltaram ao "
            f"ponto de partida: {f0:,}".replace(",", ".") + f" em {int(d.ano.iloc[0])} e "
            f"{f1:,}".replace(",", ".") + f" em {int(d.ano.iloc[-1])}, "
            f"{100*(f1-f0)/f0:+.1f}% em 18 anos. Mas a linha nao e plana: sobe ate 7.158 em "
            "2011, cai a 4.508 em 2018 e **vem subindo desde entao** (+15,5% ate 2025). "
            "Diferente da curva de sem vitimas, aqui nenhuma parte do movimento e artefato de "
            "registro: esta categoria nunca pode ser declarada pela internet.")
    else:
        d2 = d.assign(com_vitimas=d.com_feridas + d.com_fatais)
        st.plotly_chart(marcar_quebras(px.line(d2, x="ano", y="com_vitimas", markers=True,
                        title="Sinistros com vitimas por ano")), width="stretch")
        st.success("Serie comparavel em todo o periodo: os sinistros com vitimas nao foram "
                   "afetados pelas mudancas de registro de 2015 e 2018.")

    estilo.secao("Mortes e letalidade",
                 "A série de mortos é comparável em todo o período; a letalidade aparente depende do denominador.")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(marcar_quebras(px.line(d, x="ano", y="mortos", markers=True,
                        title="Mortos por ano")), width="stretch")
        m0, m1 = int(d.mortos.iloc[0]), int(d.mortos.iloc[-1])
        pico = d.loc[d.mortos.idxmax()]
        st.caption(f"**Como ler.** Cada ponto e o numero de pessoas mortas naquele ano. "
                   f"De {m0:,}".replace(",", ".") + f" em {int(d.ano.iloc[0])} para "
                   f"{m1:,}".replace(",", ".") + f" em {int(d.ano.iloc[-1])}, "
                   f"queda de {100*(m0-m1)/m0:.1f}%, com pico de "
                   f"{int(pico.mortos):,}".replace(",", ".") + f" em {int(pico.ano)}. "
                   "Esta serie **e comparavel** em todo o periodo: as mudancas de registro de "
                   "2015 e 2018 nao atingiram os sinistros com vitimas.")
    with col2:
        d3 = d.assign(letalidade=(100 * d.mortos / d.sinistros).round(2))
        st.plotly_chart(marcar_quebras(px.line(d3, x="ano", y="letalidade", markers=True,
                        title="Mortos por 100 sinistros registrados")), width="stretch")
        l0, l1 = d3.letalidade.iloc[0], d3.letalidade.iloc[-1]
        st.caption(f"**Como ler, com cuidado.** Mortos divididos pelos sinistros **registrados**. "
                   f"Sobe de {l0:.2f} para {l1:.2f} por 100 sinistros, um aumento de "
                   f"{100*(l1-l0)/l0:.0f}%. Isso **nao** significa transito mais perigoso: o "
                   "denominador perdeu os sinistros sem vitimas, entao a mesma quantidade de "
                   "mortes passa a ser dividida por uma base menor. E efeito de composicao.")
    st.info("**Por que as curvas de sinistros e de mortos parecem acompanhar uma a outra.** "
            "Elas caem no mesmo periodo por motivos diferentes: os sinistros caem 49% por "
            "mudanca de registro, os mortos caem 12,6%, que e reducao real. O grafico da direita "
            "mostra o efeito combinado: a letalidade **aparente** quase dobra, de 4,9 para 8,3 "
            "mortos por 100 sinistros, sem que o transito tenha piorado — e so a saida dos "
            "sinistros leves da base.")
    st.caption("**As marcas.** " + " - ".join(f"**{a}**: {t}" for a, t in QUEBRAS.items()))

def tela_consulta():
    estilo.cabecalho("Consulta livre",
                     "Escolha o que contar (a visão), refine pelos filtros da barra lateral e decomponha a série por "
                     "qualquer dimensão. Os números desta tela são de exploração e não vão para o texto do TCC.",
                     "Exploração · consulta com filtros")
    visao = st.radio("Visao", list(BASES), horizontal=True,
                     help="O conjunto de medidas muda com a visao: cada uma conta na sua propria chave.")
    f = montar_filtros(visao)
    base = BASES[visao]
    res = consultar(f"SELECT {MEDIDAS[visao]} FROM {base}{onde(f)}")

    primeira = res.columns[0]
    if int(res[primeira].fillna(0).iloc[0]) == 0:
        st.error("**0 resultados** para este recorte.")
        if f:
            st.write("Removendo um filtro de cada vez:")
            for nome in list(f):
                n = consultar(f"SELECT {MEDIDAS[visao]} FROM {base}{onde(f, excluir=nome)}")
                n0 = int(n[primeira].fillna(0).iloc[0])
                if n0 > 0:
                    st.button(f"remover '{nome}' -> {n0:,} resultado(s)".replace(",", "."),
                              key=f"rm_{nome}", disabled=True)
            st.caption("Os botoes indicam qual criterio zerou o recorte. "
                       "Desmarque o filtro correspondente na barra lateral.")
        return

    estilo.secao("Resultado do recorte", "Contagens da visão escolhida com todos os filtros aplicados.")
    if f:
        estilo.chips([f"{k}" for k in f])
    cols = st.columns(len(res.columns))
    for i, c in enumerate(res.columns):
        v = res[c].iloc[0]
        num = int(v) if pd.notna(v) and float(v).is_integer() else v
        cols[i].metric(c.replace("_", " "), f"{num:,}".replace(",", ".") if pd.notna(v) else "-")

    filtros_alem_periodo = [k for k in f if k != "Periodo"]
    if filtros_alem_periodo:
        tot_p = consultar(f"SELECT {PRINCIPAL[visao]} AS n FROM {base}"
                          + (f" WHERE {f['Periodo']}" if "Periodo" in f else "")).n.iloc[0]
        n_rec = consultar(f"SELECT {PRINCIPAL[visao]} AS n FROM {base}{onde(f)}").n.iloc[0]
        if tot_p:
            todos = {"Sinistros": "todos os sinistros", "Veiculos": "todos os veículos",
                     "Pessoas": "todas as pessoas", "Pares": "todos os pares"}[visao]
            st.caption(f"**Tamanho do recorte:** {100 * n_rec / tot_p:.1f}% de {todos} "
                       f"do período".replace(".", ",", 1)
                       + f" ({int(n_rec):,} de {int(tot_p):,}).".replace(",", "."))

    estilo.secao("Evolução por ano", "Escolha uma dimensão para ver a composição por cor e o tipo de gráfico.")
    expr, col_nome = PRINCIPAL[visao], NOME_PRINCIPAL[visao]
    disp = [k for k, (e, vs) in DIMENSOES.items() if vs is None or visao in vs]
    c1, c2, c3 = st.columns([2, 2, 2])
    padrao = disp.index("Tipo de acidente") if "Tipo de acidente" in disp else 0
    dim_rot = c1.selectbox("Decompor por", disp, index=padrao, key="dim",
                           help="Uma cor por valor da dimensao escolhida, ao longo dos anos. "
                                "As dimensoes marcadas (grupo) agregam em poucas familias; "
                                "as demais mostram o rotulo detalhado da PRF, harmonizado "
                                "entre as duas eras de registro.")
    dim_sql = DIMENSOES[dim_rot][0]
    tipo = c2.selectbox("Tipo de grafico", GRAFICOS if dim_sql else ["Barras", "Linhas"],
                        key="tipo_graf")

    if dim_sql:
        serie = consultar(f"""SELECT s.ano_sinistro AS ano, {dim_sql} AS categoria,
                                     {expr} AS {col_nome}
                              FROM {base}{onde(f)} GROUP BY 1,2 ORDER BY 1,2""")
        serie["categoria"] = serie.categoria.replace("", "Nao informado").fillna("Nao informado")
        serie["categoria"] = serie.categoria.map(legivel)
        soma = serie.groupby("categoria")[col_nome].sum().sort_values(ascending=False)
        n_cat = len(soma)
        if n_cat > 12:
            lim = c3.slider("Categorias no grafico", 5, min(n_cat, 60),
                            min(n_cat, 15), key="lim_cat",
                            help="Acima deste numero, as menores sao somadas em 'Outras'. "
                                 "Suba para ver todas; o grafico cresce em altura.")
            if lim < n_cat:
                manter = set(soma.head(lim).index)
                serie["categoria"] = serie.categoria.where(serie.categoria.isin(manter),
                                                           f"Outras ({n_cat - lim})")
                serie = serie.groupby(["ano", "categoria"], as_index=False)[col_nome].sum()
    else:
        serie = consultar(f"""SELECT s.ano_sinistro AS ano, {expr} AS {col_nome}
                              FROM {base}{onde(f)} GROUP BY 1 ORDER BY 1""")

    if len(serie) > 1:
        rot = {col_nome: col_nome.capitalize(), "categoria": dim_rot, "pct": "% do ano"}
        titulo = f"{col_nome.capitalize()} por ano"
        if dim_sql:
            titulo += f", por {dim_rot.lower()}"
            if tipo == "Barras empilhadas":
                fig = px.bar(serie, x="ano", y=col_nome, color="categoria", barmode="stack",
                             title=titulo, labels=rot)
            elif tipo == "Linhas":
                fig = px.line(serie, x="ano", y=col_nome, color="categoria", markers=True,
                              title=titulo, labels=rot)
            elif tipo.startswith("Area 100"):
                tot_ano = serie.groupby("ano")[col_nome].transform("sum")
                serie["pct"] = (100 * serie[col_nome] / tot_ano).round(2)
                fig = px.area(serie, x="ano", y="pct", color="categoria",
                              title=f"Composicao por {dim_rot.lower()}, em % de cada ano",
                              labels=rot)
                fig.update_yaxes(range=[0, 100], ticksuffix="%")
            else:
                m = (serie.groupby(["categoria", "ano"], as_index=False)[col_nome].sum()
                          .pivot(index="categoria", columns="ano", values=col_nome).fillna(0))
                m = m.loc[m.sum(axis=1).sort_values(ascending=False).index]
                fig = px.imshow(m, aspect="auto", color_continuous_scale="Blues",
                                title=f"{titulo} (mapa de calor)",
                                labels={"color": col_nome.capitalize()})
        else:
            fig = (px.line if tipo == "Linhas" else px.bar)(
                serie, x="ano", y=col_nome, title=titulo, labels=rot,
                **({"markers": True} if tipo == "Linhas" else {}))
        if not tipo.startswith("Mapa"):
            fig.update_yaxes(rangemode="tozero")
        n_leg = serie.categoria.nunique() if dim_sql else 1
        fig.update_layout(height=max(430, min(430 + 22 * max(0, n_leg - 8), 1100)),
                          legend_title_text=dim_rot if dim_sql else None)
        for ano in QUEBRAS:
            if serie.ano.min() <= ano <= serie.ano.max() and not tipo.startswith("Mapa"):
                fig.add_vline(x=ano, line_dash="dot", line_color="#b00", opacity=.45)
        st.plotly_chart(fig, width="stretch")

        fmt = lambda n: f"{int(n):,}".replace(",", ".")
        tot = int(serie[col_nome].sum())
        a0, a1 = int(serie.ano.min()), int(serie.ano.max())
        if dim_sql:
            sm = serie.groupby("categoria")[col_nome].sum().sort_values(ascending=False)
            top = sm.index[0]
            ini_pct = 100 * serie[(serie.ano == a0) & (serie.categoria == top)][col_nome].sum() / \
                      max(serie[serie.ano == a0][col_nome].sum(), 1)
            fim_pct = 100 * serie[(serie.ano == a1) & (serie.categoria == top)][col_nome].sum() / \
                      max(serie[serie.ano == a1][col_nome].sum(), 1)
            txt = (f"**Como ler.** Cada cor e um valor de *{dim_rot.lower()}*. "
                   f"Total do recorte: {fmt(tot)} entre {a0} e {a1}, em {len(sm)} categorias. "
                   f"A maior e **{top}**, com {fmt(sm.iloc[0])} ({100*sm.iloc[0]/tot:.1f}% do total) "
                   f"— passou de {ini_pct:.1f}% dos casos em {a0} para {fim_pct:.1f}% em {a1}.")
            if tipo.startswith("Area 100"):
                txt += (" Esta vista mostra **proporcao**, nao volume: por isso ela e comparavel "
                        "ao longo do tempo mesmo com a base mudando de tamanho em 2015 e 2018.")
            elif tipo.startswith("Mapa"):
                txt += " Quanto mais escura a celula, maior o valor naquele ano."
            else:
                txt += " O eixo vertical se ajusta a este recorte."
            st.caption(txt)
        else:
            st.caption(f"**Como ler.** Total do recorte: {fmt(tot)} entre {a0} e {a1}. "
                       "O eixo vertical se ajusta a este recorte. Escolha uma dimensao em "
                       "**Decompor por** para ver a composicao por cor.")

    if visao in ("Pares", "Veiculos"):
        estilo.secao("Detalhamento", "As 50 combinações mais frequentes do recorte.")
    if visao == "Pares":
        d = consultar(f"""SELECT r.fabricante, r.familia AS modelo, r.contraparte_tipo AS contraparte_tipo,
                                 r.fabricante_cp, r.familia_cp AS contraparte, count(*) AS pares,
                                 count(DISTINCT (s.ano_sinistro || '-' || s.id)) AS sinistros
                          FROM {base}{onde(f)} GROUP BY 1,2,3,4,5 ORDER BY pares DESC LIMIT 50""")
        st.dataframe(d, width="stretch")
    elif visao == "Veiculos":
        d = consultar(f"""SELECT v.fabricante, v.familia AS modelo, v.geracao_rotulo AS geracao, v.faixa_ano_fab AS faixa,
                                 count(DISTINCT (v.ano_sinistro || '-' || v.id_veiculo)) AS veiculos,
                                 sum(CASE WHEN v.severidade_veiculo='obito' THEN 1 ELSE 0 END) AS com_obito
                          FROM {base}{onde(f)} GROUP BY 1,2,3,4 ORDER BY veiculos DESC LIMIT 50""")
        st.dataframe(d, width="stretch")

    av = avisos(f, visao)
    if av:
        estilo.secao("Cuidados de leitura deste recorte")
    for a in av:
        st.warning(a)

PAGINAS = {"Inicio": "Início", "Analise do TCC": "Análise do TCC", "Panorama": "Panorama",
           "Consulta livre": "Consulta livre", "Perguntas": "Perguntas", "Fontes e metodo": "Fontes e método"}
estilo.marca_lateral()
pagina = st.sidebar.radio("Navegação", list(PAGINAS), format_func=PAGINAS.get, key="pagina")
st.sidebar.divider()
if not fonte_disponivel():
    st.error("Os dados do painel não estão disponíveis.")
elif pagina == "Inicio":
    from inicio import tela_inicio
    tela_inicio(consultar)
elif pagina == "Fontes e metodo":
    from metodologia import tela_metodologia
    tela_metodologia(QUEBRAS)
elif pagina == "Panorama":
    tela_panorama()
elif pagina == "Analise do TCC":
    from analise_tcc import tela_analise_tcc
    tela_analise_tcc()
elif pagina == "Perguntas":
    from perguntas import tela_perguntas
    tela_perguntas(consultar)
else:
    tela_consulta()
