import json, pathlib, pandas as pd, streamlit as st
import estilo

R = pathlib.Path(__file__).resolve().parents[3]
FLUXO = R / "03_dados" / "08_populacao" / "fluxograma_inclusao.json"
GER = R / "08_resultados" / "tabelas" / "geracoes" / "GERACOES_v1_completa.csv"
URL_PRF = "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf"
n = lambda v: f"{int(v):,}".replace(",", ".")

def tela_metodologia(quebras):
    estilo.cabecalho("Fontes e método", "De onde vêm os dados, que período cada parte do painel cobre, como as "
                     "medidas foram definidas e o que os dados não permitem afirmar.", "Sobre o painel")

    estilo.secao("Fonte dos dados")
    st.markdown(f"- **[Dados abertos da Polícia Rodoviária Federal]({URL_PRF})**: um arquivo por ano agrupado por "
                "ocorrência (uma linha por sinistro) e outro agrupado por pessoa (uma linha por pessoa envolvida, com "
                "o veículo em que estava, marca e modelo, ano de fabricação, papel e estado físico).\n"
                "- O significado de cada campo foi conferido nos dicionários de variáveis oficiais dos dois sistemas "
                "de registro que a PRF usou no período.\n"
                "- Os arquivos originais são preservados sem alteração, com assinatura digital (SHA-256); todo "
                "tratamento gera uma versão derivada e documentada.")

    estilo.secao("Período de cada parte do painel")
    st.markdown("| Parte do painel | Período | Observação |\n|---|---|---|\n"
                "| Panorama | 2008–2025 | Sinistros e mortes por ano. De 2008 a 2012, contagens do arquivo publicado por ocorrência. |\n"
                "| Consulta livre e Perguntas | 2013–2025 | Veículos, pessoas e pares de veículos existem a partir de 2013. |\n"
                "| Análise do TCC | 2019–2025 | Primeiro ano completo depois das mudanças de registro de 2015 e 2018, "
                "inteiramente no sistema de registro adotado em 2017. |")

    estilo.secao("Duas formas de ler os mesmos dados",
                 "O painel tem uma parte de exploração e uma parte que reproduz a análise do trabalho.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        estilo.card("<h4>Exploração (Panorama, Consulta livre, Perguntas)</h4><div class='txt'>Regime inclusivo: "
                    "registros com informação ausente permanecem, e a ausência aparece como categoria visível, nunca "
                    "como zero ou linha omitida. Nada é imputado. Os números desta parte não vão para o texto do TCC.</div>")
    with c2:
        estilo.card("<h4>Análise do TCC</h4><div class='txt'>Uma população definida por critérios aplicados em "
                    "sequência. A tela só lê as tabelas produzidas pela análise; não recalcula nada. Na Consulta livre, "
                    "o filtro <b>Recorte do TCC</b> reproduz exatamente essa população, conferida por teste automático "
                    "a cada reconstrução do painel.</div>")
    if FLUXO.exists():
        fl = json.load(open(FLUXO, encoding="utf-8"))
        tot = {k: sum(x[k] for x in fl) for k in fl[0] if k != "ano"}
        etapas = [("Pessoas registradas, 2019–2025", "0_pessoas"), ("Ocupantes (condutor ou passageiro)", "1_ocupantes"),
                  ("Em automóvel", "2_em_automovel"), ("Com estado físico informado", "3_desfecho_conhecido"),
                  ("Com ano de fabricação válido", "4_ano_fab_valido"), ("Com modelo identificado", "5_modelo_identificado")]
        f = pd.DataFrame([{"Critério": e, "Restam": n(tot[k])} for e, k in etapas])
        with st.expander("Critérios de inclusão da população da análise"):
            st.dataframe(f, hide_index=True, width="stretch")

    estilo.secao("Definições")
    ng = nf = None
    if GER.exists():
        g = pd.read_csv(GER, sep=";", dtype=str); ng, nf = len(g), g.familia.nunique()
    st.markdown(
        "- **Unidade de análise:** o ocupante de automóvel, condutor ou passageiro.\n"
        "- **Gravidade:** o estado físico registrado pela PRF no local (ileso, lesões leves, lesões graves, óbito). "
        "As comparações usam a proporção de **óbito ou lesão grave**.\n"
        "- **Tipo de colisão:** definido pelos veículos presentes no sinistro (automóvel sozinho, com veículo leve, "
        "com motocicleta, com caminhão, com ônibus etc.). Descreve o ambiente da colisão, não o par de impacto.\n"
        "- **Faixa de fabricação:** antes de 2000, 2000–2009, 2010–2014, 2015–2019 e 2020 em diante.\n"
        "- **Modelo:** fabricante e família, identificados a partir do texto livre do registro"
        + (f"; nas {nf} famílias com volume para comparação, também a **geração** ({ng} gerações, definidas pela "
           "plataforma do veículo). Quando o ano de fabricação cabe em duas gerações e o texto não resolve, o veículo "
           "fica marcado como geração ambígua e não é comparado." if ng else ".") + "\n"
        "- **Contexto da via:** tipo de pista (simples, dupla, múltipla) e trecho urbano ou rural, como registrados.")

    estilo.secao("Mudanças de registro que afetam as séries")
    for ano, txt in quebras.items():
        st.markdown(f"- **{ano}:** {txt}.")
    st.caption("Os totais de sinistros não são comparáveis antes e depois de 2015 e 2018: a queda está concentrada nos "
               "sinistros sem vítimas e decorre da forma de registro. As séries de mortos e de sinistros com vítimas "
               "não foram afetadas.")

    estilo.secao("O que os dados não permitem afirmar")
    st.markdown(
        "- **Sem exposição:** não há frota circulante nem quilometragem por modelo; nada se pode afirmar sobre a "
        "frequência de envolvimento em sinistros nem sobre a segurança intrínseca de um modelo.\n"
        "- **Confundimento:** massa, velocidade, uso de cinto, conservação e perfil de uso não estão nos dados.\n"
        "- **Desfecho no local:** o estado físico é o registrado no atendimento, sem a evolução clínica posterior.\n"
        "- **Seleção:** os ocupantes sem estado físico informado não são uma perda aleatória.\n"
        "- **Cobertura:** rodovias federais e automóveis; os resultados não se estendem a vias urbanas, motocicletas "
        "ou veículos pesados.\n"
        "- **Associação, não causa:** todas as diferenças apresentadas são associações observadas.")

    estilo.secao("Reprodutibilidade")
    st.markdown("Todo o tratamento é feito por scripts versionados, executados em sequência por um orquestrador, a "
                "partir dos arquivos originais. Cada decisão metodológica está registrada com justificativa, regra e "
                "impacto. Testes automáticos conferem a integridade dos dados do painel e a igualdade entre o recorte "
                "do TCC no painel e a população da análise.")
