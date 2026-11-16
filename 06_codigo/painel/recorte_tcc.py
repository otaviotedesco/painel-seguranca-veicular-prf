CONDICOES = [
    "p.ano_sinistro BETWEEN 2019 AND 2025",
    "p.papel = 'ocupante'",
    "v.tipo_veiculo = 'Automóvel'",
    "p.desfecho IN ('ileso','lesoes_leves','lesoes_graves','obito')",
    "v.faixa_ano_fab <> 'nao_informado'",
    "v.familia NOT IN ('INDETERMINADO','NAO_IDENTIFICADO')",
]
SQL = " AND ".join(CONDICOES)
N_ESPERADO = 427_739
