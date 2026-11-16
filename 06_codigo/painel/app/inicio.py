"""Pagina inicial do painel (DP-52). Apresenta o trabalho e conduz a exploracao.
Todo numero desta pagina e lido do banco do painel ou do fluxograma do TCC no momento da exibicao; nenhum e
digitado. Os textos repetem o que o documento do TCC ja afirma (titulo, objetivo, delimitacao)."""
import json, pathlib, streamlit as st
import estilo

R = pathlib.Path(__file__).resolve().parents[3]
FLUXO = R / "03_dados" / "08_populacao" / "fluxograma_inclusao.json"
URL_PRF = "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf"
n = lambda v: f"{int(v):,}".replace(",", ".")

def _ir(pagina):
    st.session_state["pagina"] = pagina

def tela_inicio(consultar):
    st.markdown(
        '<div class="tcc-hero"><div class="sob">Trabalho de Conclusão de Curso · IFRS Campus Veranópolis · '
        'Análise e Desenvolvimento de Sistemas</div>'
        '<h1>Análise de dados aplicada à segurança veicular em condições reais de trânsito</h1>'
        '<div class="sub">Distribuição da gravidade das lesões de ocupantes de automóveis segundo o modelo e o ano '
        'de fabricação do veículo, em sinistros registrados nas rodovias federais brasileiras.</div>'
        '<div class="aut">Otávio Rizzatti Tedesco · Orientador: Prof. Me. Marcos Corino · 2026</div></div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown("#### O tema")
        st.markdown("Ensaios de laboratório, como os do Latin NCAP, avaliam a proteção dos veículos em condições "
                    "controladas. Este trabalho olha para os sinistros que de fato acontecem: como a gravidade das "
                    "lesões se distribui entre os ocupantes de automóveis quando toda a variedade das colisões reais "
                    "está presente.")
        st.markdown("#### Objetivo geral")
        st.markdown("Analisar como a gravidade das lesões dos ocupantes de automóveis se distribui entre modelos de "
                    "veículos e se associa ao ano de fabricação, em sinistros registrados pela Polícia Rodoviária "
                    "Federal nas rodovias federais brasileiras, disponibilizando os resultados neste painel.")
    with c2:
        st.markdown("#### Os dados")
        st.markdown(f"Dados abertos da **[Polícia Rodoviária Federal]({URL_PRF})**: um registro por sinistro e um "
                    "por pessoa envolvida, com o veículo, o modelo, o ano de fabricação e o estado físico de cada pessoa.")
        estilo.chips(["Série de sinistros: 2008–2025", "Veículos e pessoas: 2013–2025",
                      "Análise do TCC: 2019–2025"])

    d = consultar("""SELECT sum(sinistros) AS sinistros, sum(mortos) AS mortos, min(ano) AS a0, max(ano) AS a1 FROM
                     (SELECT ano_sinistro AS ano, count(DISTINCT id) AS sinistros, sum(n_mortos) AS mortos
                      FROM fato_sinistro GROUP BY 1)""").iloc[0]
    k = st.columns(4)
    with k[0]: estilo.card_valor("Sinistros registrados", n(d.sinistros), f"rodovias federais, {int(d.a0)}–{int(d.a1)}")
    with k[1]: estilo.card_valor("Mortos", n(d.mortos), f"registrados, {int(d.a0)}–{int(d.a1)}")
    if FLUXO.exists():
        fl = json.load(open(FLUXO, encoding="utf-8"))
        oc = sum(x["5_modelo_identificado"] for x in fl); gr = sum(x["6_obito_ou_grave"] for x in fl)
        with k[2]: estilo.card_valor("Ocupantes na análise", n(oc), "de automóveis, 2019–2025")
        with k[3]: estilo.card_valor("Óbito ou lesão grave", f"{100 * gr / oc:.2f}%".replace(".", ","),
                                     "entre os ocupantes analisados")

    st.markdown("#### O que você encontra no painel")
    paginas = [("Analise do TCC", "Análise do TCC", "Resultados do trabalho: gravidade por tipo de colisão, ano "
                "de fabricação, contexto da via e modelo, com os números do texto."),
               ("Panorama", "Panorama", "A série histórica dos sinistros e das mortes nas rodovias federais, com as "
                "mudanças de registro que afetam a leitura."),
               ("Consulta livre", "Consulta livre", "Exploração com filtros por período, local, tipo de sinistro, "
                "veículo, modelo, geração e pessoa."),
               ("Perguntas", "Perguntas", "Respostas prontas a dez perguntas sobre colisões, causas, horários e trechos."),
               ("Fontes e metodo", "Fontes e método", "De onde vêm os dados, os períodos, as definições e os limites "
                "de interpretação.")]
    cols = st.columns(len(paginas))
    for c, (chave, nome, txt) in zip(cols, paginas):
        with c:
            estilo.card(f"<h4>{nome}</h4><div class='txt'>{txt}</div>", "nav")
            st.button(f"Abrir {nome.lower()}" if chave != "Analise do TCC" else "Abrir a análise",
                      key=f"ir_{chave}", on_click=_ir, args=(chave,), width="stretch",
                      type="primary" if chave == "Analise do TCC" else "secondary")

    st.info("**Como ler.** Os dados descrevem o que aconteceu **depois** que o sinistro ocorreu. Não há informação sobre "
            "quantos veículos de cada modelo circulam nem quanto rodam; por isso nada no painel indica que um modelo "
            "se envolve mais em sinistros ou que seja intrinsecamente mais seguro. As diferenças são associações, "
            "não causas.", icon="ℹ️")
