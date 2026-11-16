# Painel — gravidade das lesões de ocupantes de automóveis nas rodovias federais

Painel interativo do Trabalho de Conclusão de Curso *Análise de dados aplicada à segurança veicular em condições
reais de trânsito* (IFRS Campus Veranópolis, Análise e Desenvolvimento de Sistemas, 2026), de Otávio Rizzatti
Tedesco, com orientação do Prof. Me. Marcos Corino.

O painel apresenta a análise do trabalho e permite explorar os dados de sinistros registrados pela Polícia
Rodoviária Federal (PRF) nas rodovias federais brasileiras.

## Fonte dos dados
[Dados abertos da Polícia Rodoviária Federal](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf).
Os arquivos de `03_dados/09_painel/` são uma camada derivada desses dados, com rótulos harmonizados entre os sistemas
de registro e o modelo do veículo identificado a partir do texto livre do registro. Os demais arquivos são as tabelas
de resultado que a tela "Análise do TCC" exibe.

## Como ler
Os dados descrevem o que aconteceu depois que o sinistro ocorreu. Não há informação sobre quantos veículos de cada
modelo circulam nem quanto rodam; por isso nada no painel indica que um modelo se envolve mais em sinistros ou que
seja intrinsecamente mais seguro. As diferenças são associações, não causas.

## Executar localmente
```
pip install -r requirements.txt
streamlit run 06_codigo/painel/app/painel.py
```
Na primeira abertura, o painel monta um banco DuckDB temporário a partir dos arquivos Parquet.

## Conteúdo
Este repositório contém apenas o necessário para o painel funcionar. A lista de arquivos, com o motivo de cada um
e sua assinatura SHA-256, está em `MANIFESTO.json`.
