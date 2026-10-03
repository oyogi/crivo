# De onde vêm os textos

O experimento usa o [B2W-Reviews01](https://github.com/americanas-tech/b2w-reviews01),
de Livy Real, Marcio Oshiro e Alexandre Mafra / B2W Digital. São avaliações
da Americanas.com, de janeiro a maio de 2018. A fonte tem 132.373 linhas.
Não são avaliações de restaurantes nem dados do iFood.

- Revisão fixada: `4639429ec698d7821fc99a0bc665fa213d9fcd5a`.
- Arquivo: `B2W-Reviews01.csv`, 49.453.175 bytes.
- SHA-256: `821fb0bf9f7230b0fba4e4f9fadd75a66d1a9ff0b1657810791d33007eb2ab38`.
- Licença: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

O download é feito do arquivo original, com checksum. O CSV não vai para o Git.
Nesta revisão o delimitador é **vírgula**, apesar da orientação diferente no
README da fonte. Não publique esse material como se fosse uma base própria.
Modelos e relatórios derivados deste corpus ficam sob CC BY-NC-SA 4.0;
a licença MIT do código não libera os dados para uso comercial.

## O que entra no experimento

Só `review_text` vira feature. A nota gera o alvo: 1–2 = negativa; 4–5 = positiva.
`product_id` serve apenas para separar os conjuntos. Não uso título, marca,
recomendação, identidade, idade, gênero ou localização como entrada do modelo.
As notas são um atalho de rotulagem e podem discordar do texto.

Textos vazios são removidos. Para detectar duplicatas, normalizo Unicode,
caixa, pontuação e espaços. Guardo a primeira ocorrência de cada texto;
se o mesmo texto aparece com classes diferentes, removo o grupo inteiro.
Três estrelas conta como uma classe separada só nessa limpeza.
Isso evita que um “muito bom” repetido vire treino e teste ao mesmo tempo.
Não detecto paráfrases nem duplicatas aproximadas.

Um hash estável de `product_id` define treino/validação/teste em cerca de
70/15/15% dos **produtos**, não necessariamente das linhas. Não há estratificação
por classe. Três estrelas fica fora do treino e da seleção; apenas as avaliações
de três estrelas de produtos do teste compõem um diagnóstico adicional.
Não chamo esse grupo de neutro: três estrelas também pode conter opinião forte.

O split mede generalização para outros produtos da mesma fonte. Não separa
autores, lojas ou datas, e não mede generalização para delivery em 2026.
O arquivo bruto contém informações de perfil. O projeto não as copia para
relatórios e não precisa delas para treinar. Os relatórios de erro mostram
linha, nota e score, sem reproduzir o texto original.

Referência: Real, L.; Oshiro, M.; Mafra, A. (2019).
*B2W-Reviews01: An Open Product Reviews Corpus*. STIL.
