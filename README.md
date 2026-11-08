# Perguntas em régua, ao vivo

O público lê o QR code e, no celular, marca cada pergunta numa régua que vai
de **Não** (esquerda) a **Sim** (direita). A barra fica vermelha perto do Não,
amarela no meio e verde perto do Sim. O painel projetado mostra, para cada
pergunta, a média das respostas numa régua de 0% a 100% e se atualiza sozinho
a cada 3 segundos.

| Endereço | Para quê |
|---|---|
| `/` | o painel: projetar em tela cheia (F11); `?tema=escuro` para fundo escuro |
| `/r` | página de resposta, para onde o QR leva |
| `/admin` | editar as perguntas, ver médias, limpar as respostas, baixar o QR |
| `/api/resultado` | médias em JSON |
| `/qr.png?baixar=1` | QR em alta resolução para slide ou impressão |

No painel o QR fica no canto inferior direito; clique nele para ampliar.
`qr-perguntas.png`/`.svg` (QR simples) e `qr-apresentacao.png` (com o endereço
escrito embaixo), na raiz, já apontam para
`https://perguntas.agilematuritymodel.com/r` e servem para montar slide antes
do deploy.

## Como a resposta vira média

- Cada régua guarda a posição de 0 (Não) a 100 (Sim). A média da pergunta é a
  média dessas posições: 0% é todo mundo no Não; 100%, todo mundo no Sim.
- A régua começa sem marcação, e o botão só libera com todas tocadas. Assim
  ninguém entra na média com um 50 que não escolheu.
- No celular, rolar a página passando o dedo por cima de uma régua não marca
  nada; marca o toque parado ou o deslize para o lado.

## Uma resposta por pessoa

Mesmo esquema da nuvem de palavras: na primeira resposta o navegador recebe um
cookie, e quem abrir o QR de novo vê "Você já respondeu" com o que marcou. É
por navegador, não à prova de fraude (janela anônima responde outra vez); por
IP não serviria, porque no escritório todo mundo sai pelo mesmo IP.

**Limpar todas** no `/admin` começa uma rodada nova: todos podem responder de
novo.

## Perguntas

As 5 perguntas iniciais entram no primeiro boot (`PERGUNTAS_PADRAO` em
`app/db.py`). Depois quem manda é o `/admin`: uma pergunta por linha, até 10.
A edição é por posição: corrigir o texto da linha 3 mantém as respostas da
pergunta 3; apagar uma linha apaga as respostas dela; linhas novas entram
vazias. Trocar uma pergunta por outra completamente diferente sem limpar
mantém as respostas antigas naquela posição, então para mudar o conteúdo use
**Limpar todas** antes.

## Rodar local

`run.bat` cria o `.venv` na primeira vez e sobe em http://127.0.0.1:8011
(admin: qualquer usuário, senha `admin`).

## Variáveis

| Variável | O que faz | Padrão |
|---|---|---|
| `DATA_DIR` | pasta do SQLite (`/data` no Railway) | `./data` |
| `ADMIN_PASSWORD` | senha do `/admin`; sem ela o `/admin` fica desligado | — |
| `URL_PUBLICA` | domínio que vai no QR | host da requisição |

Publicação: [DEPLOY.md](DEPLOY.md).
