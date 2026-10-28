# Verificação

Executado localmente em 28/10/2026, Linux e Python 3.14.8:

- Ambiente resolvido e sincronizado com `uv sync --locked`.
- Treino completo com revisão e SHA-256 do B2W conferidos.
- Partições registradas por contagem e hash das linhas originais em `metrics.json`.
- Testes de limpeza, isolamento, política, explicações, CLI e HTTP.
- Integração offline: CSV, treino, seleção, artefato salvo, carregamento e predição.
- Wheel e sdist construídos com `uv build`; wheel instalado em ambiente isolado.
- Interface conferida no navegador em desktop e celular, com exemplos reais.
- Gráficos calculados diretamente dos relatórios, UML renderizado com PlantUML.

A CI confere estilo, testes, build e o pacote instalado em Python 3.12 e 3.14. O histórico de execuções
fica na [aba Actions](https://github.com/oyogi/crivo/actions).
