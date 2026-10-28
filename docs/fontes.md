# Fontes e imagens

Capturas feitas em 28/10/2026. São páginas e execuções reais; não há mockups
nem imagens geradas. Fotos, marcas e interfaces externas pertencem aos seus
titulares e não estão cobertas pela licença MIT do código.

| Imagem | Origem e papel no projeto |
|---|---|
| `images/crivo-desktop.jpg` e `images/crivo-mobile.jpg` | Aplicação local executando o modelo treinado; exemplo original do corpus. |
| `images/americanas.jpg` | [Americanas — eletrodomésticos](https://www.americanas.com.br/eletrodomesticos). Contexto atual do varejista de origem do corpus; preços e catálogo podem mudar. |
| `images/mercado-livre.jpg` | [Mercado Livre — opiniões de produtos](https://developers.mercadolivre.com.br/pt_br/opinioes-sobre-um-produto). Referência de uma API real com texto e estrelas. Nenhuma integração autenticada ou avaliação nesse site é alegada. |
| `images/cobertura.png` e `images/confusao.png` | Calculadas por `scripts/figures.py` usando `reports/metrics.json` e `risk_coverage.csv`. |
| `architecture.svg` | Renderização PlantUML MIT 1.2026.9 de `diagrams.uml`. |

Os três exemplos da aplicação vêm do [CSV original fixado](https://github.com/americanas-tech/b2w-reviews01/blob/4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv):

| Linha | Produto | Nota | Texto original |
|---|---|---|---|
| 14 | 29302228 | 5 | Jogo de panelas excelente material, entrega a tempo, design muito bom. |
| 79 | 27818579 | 1 | O produto é completamente diferente da descrição e da foto. Não recomendo. |
| 345 | 14738991 | 3 | O produto é bom, mas um dos espelhos veio quebrado |

A linha é contada no arquivo original, incluindo o cabeçalho. Esses exemplos
servem para inspecionar o comportamento; não são uma amostra aleatória de
avaliação nem um teste externo. Nota 3 não define um alvo binário correto.
Atribuição: Real, Oshiro e Mafra / B2W Digital, CC BY-NC-SA 4.0.
