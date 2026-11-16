"""Recorte do TCC na camada do painel (DM-058) — definicao unica, usada pelo app e pelo teste do p04.

Reproduz a populacao analitica do TCC (DM-053, DM-059): ocupante de automovel, 2019-2025,
desfecho conhecido, ano de fabricacao valido, modelo identificado. Prefixos: p = fato_pessoa,
v = fato_veiculo, s = fato_sinistro. Conferido em 2026-11-07: 427.739 ocupantes, identicos
linha a linha a 03_dados/08_populacao/populacao_analitica.csv.gz (chaves, desfecho, familia,
fabricante, faixa de fabricacao e UF).
"""
CONDICOES = [
    "p.ano_sinistro BETWEEN 2019 AND 2025",                                   # DM-040
    "p.papel = 'ocupante'",                                                   # DM-037
    "v.tipo_veiculo = 'Automóvel'",                                           # DM-039
    "p.desfecho IN ('ileso','lesoes_leves','lesoes_graves','obito')",         # DM-038
    "v.faixa_ano_fab <> 'nao_informado'",                                     # DM-045, DM-050
    "v.familia NOT IN ('INDETERMINADO','NAO_IDENTIFICADO')",                  # DM-052, DM-059
]
SQL = " AND ".join(CONDICOES)
N_ESPERADO = 427_739          # DM-053 REVISAO 1
