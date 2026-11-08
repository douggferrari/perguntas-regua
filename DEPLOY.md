# Publicar em perguntas.agilematuritymodel.com

Mesmo caminho da nuvem de palavras: GitHub → Railway → DNS na Hostinger.

## 1. GitHub

Criar um repositório **vazio** (sem README) em github.com, por exemplo
`douggferrari/perguntas-regua`. Depois, nesta pasta:

```bash
git init -b main
git add .
git commit -m "Perguntas em régua ao vivo (v1.0)"
git remote add origin https://github.com/douggferrari/perguntas-regua.git
git push -u origin main
```

## 2. Railway

1. No projeto da nuvem (`proactive-integrity`): **+ Create → GitHub Repo →
   perguntas-regua**. O `railway.json` já define o start.
2. No serviço novo: **+ New Volume** montado em `/data`. Sem volume, cada
   deploy apaga as respostas.
3. **Variables**:

   | Variável | Valor |
   |---|---|
   | `DATA_DIR` | `/data` |
   | `ADMIN_PASSWORD` | uma senha forte para o `/admin` |
   | `URL_PUBLICA` | `https://perguntas.agilematuritymodel.com` |

4. **Settings → Networking → Custom Domain** →
   `perguntas.agilematuritymodel.com`. O Railway mostra dois registros DNS;
   anote os valores.

## 3. Hostinger (hPanel → Domínios → agilematuritymodel.com → DNS)

| Tipo | Nome | Valor |
|---|---|---|
| CNAME | `perguntas` | o `xxxx.up.railway.app` mostrado pelo Railway |
| TXT | `_railway-verify.perguntas` | o valor mostrado pelo Railway |

Só o CNAME não basta: sem o TXT o Railway não valida o domínio. Na nuvem, o
domínio validou uns 3 minutos depois do DNS, e o certificado HTTPS saiu uns 10
minutos depois disso. Antes do certificado o celular avisa "não seguro".

## 4. Conferir

- No celular, **com dados móveis** e em janela anônima: ler
  `qr-perguntas.png`, marcar as réguas e ver as médias mudarem em
  `https://perguntas.agilematuritymodel.com`. Depois, **Limpar todas** no
  `/admin`. No PC, o Avast pode marcar o site como "não seguro" mesmo com
  tudo certo.
- Versão no ar, sem logar:

  ```bash
  curl -s https://perguntas.agilematuritymodel.com/ | grep -o 'estilo.css?v=[0-9.]*'
  ```

  O número é o `VERSAO` de `app/main.py`; suba esse número a cada mudança.

Se o push entra e o site continua na versão antiga, olhar o billing do Railway
primeiro: ele pausa build e mantém o container velho no ar.

## Antes de cada sessão

`/admin` → conferir as perguntas → **Limpar todas**, que também libera todo
mundo para responder de novo.
