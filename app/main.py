"""Régua ao vivo: o público lê o QR, responde Não ou Sim a cada pergunta em /r
e o painel em / mostra quantos % responderam Sim, numa régua de 0% a 100%."""
import io
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import segno
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db

VERSAO = "1.1"
BASE = Path(__file__).resolve().parent
# Identifica a pessoa para valer "uma resposta por pessoa". É por navegador:
# janela anônima burla, mas IP não serve (no escritório todos saem pelo mesmo).
COOKIE_PESSOA = "perguntas_pessoa"
UM_ANO = 365 * 24 * 3600


@asynccontextmanager
async def ciclo_de_vida(_app):
    db.criar_esquema()
    yield


app = FastAPI(lifespan=ciclo_de_vida, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals["versao"] = VERSAO


def url_resposta(request: Request) -> str:
    """Endereço que vai no QR. URL_PUBLICA fixa o domínio; sem ela, vale o host
    da requisição (no Railway, abrir pelo *.up.railway.app geraria QR errado)."""
    base = os.environ.get("URL_PUBLICA") or str(request.base_url)
    return base.rstrip("/") + "/r"


def pagina(request: Request, nome: str, status_code: int = 200, **contexto):
    return templates.TemplateResponse(request, nome, contexto, status_code=status_code)


def perguntas_atuais() -> list[dict]:
    with db.conectar() as con:
        return db.perguntas(con)


def respostas_da_pessoa(request: Request) -> list[dict] | None:
    pessoa = request.cookies.get(COOKIE_PESSOA)
    if not pessoa:
        return None
    with db.conectar() as con:
        return db.respostas_de(con, pessoa)


def ler_valores(form, perguntas: list[dict]) -> dict[int, int] | None:
    """0 (Não) ou 100 (Sim) para cada pergunta, ou None se faltar algum. O campo
    só vai no POST depois que a pessoa escolhe um lado (ver responder.js)."""
    valores = {}
    for p in perguntas:
        try:
            valor = int(form.get(f"p{p['id']}", ""))
        except (TypeError, ValueError):
            return None
        if valor not in (0, 100):
            return None
        valores[p["id"]] = valor
    return valores


# ---------- público ----------

@app.get("/")
def painel(request: Request):
    url_curta = url_resposta(request).split("://", 1)[-1]
    return pagina(request, "painel.html", url_curta=url_curta)


@app.get("/api/resultado")
def api_resultado():
    with db.conectar() as con:
        dados = {"total": db.total_respostas(con), "perguntas": db.resultado(con)}
    return JSONResponse(dados, headers={"Cache-Control": "no-store"})


@app.get("/r")
def responder(request: Request):
    suas = respostas_da_pessoa(request)
    if suas is not None:
        return pagina(request, "obrigado.html", respostas=suas, ja_respondeu=True)
    return pagina(request, "responder.html", perguntas=perguntas_atuais())


@app.post("/r")
async def enviar(request: Request):
    perguntas = perguntas_atuais()
    valores = ler_valores(await request.form(), perguntas)
    if valores is None:
        return pagina(request, "responder.html", status_code=422, perguntas=perguntas,
                      erro="Responda todas as perguntas antes de enviar.")
    pessoa = request.cookies.get(COOKIE_PESSOA, "")[:64] or secrets.token_urlsafe(16)
    with db.conectar() as con:
        registrada = db.adicionar(con, pessoa, valores)
    # Quem já tinha respondido volta para /r, que mostra as respostas originais.
    destino = RedirectResponse("/r/obrigado" if registrada else "/r", status_code=303)
    destino.set_cookie(COOKIE_PESSOA, pessoa, max_age=UM_ANO, httponly=True, samesite="lax",
                       secure=request.url.scheme == "https")
    return destino


@app.get("/r/obrigado")
def obrigado(request: Request):
    return pagina(request, "obrigado.html", respostas=respostas_da_pessoa(request),
                  ja_respondeu=False)


@app.get("/qr.svg")
def qr_svg(request: Request):
    buf = io.BytesIO()
    segno.make(url_resposta(request), error="m").save(
        buf, kind="svg", border=2, omitsize=True, xmldecl=False)
    return Response(buf.getvalue(), media_type="image/svg+xml")


@app.get("/qr.png")
def qr_png(request: Request, baixar: bool = False):
    buf = io.BytesIO()
    segno.make(url_resposta(request), error="m").save(buf, kind="png", scale=20, border=4)
    headers = {"Content-Disposition": 'attachment; filename="qr-perguntas.png"'} if baixar else {}
    return Response(buf.getvalue(), media_type="image/png", headers=headers)


# ---------- admin ----------

_basic = HTTPBasic(auto_error=False)


def exigir_admin(cred: HTTPBasicCredentials | None = Depends(_basic)):
    senha = os.environ.get("ADMIN_PASSWORD")
    if not senha:
        raise HTTPException(503, "Defina ADMIN_PASSWORD para liberar o /admin.")
    if cred is None or not secrets.compare_digest(cred.password.encode(), senha.encode()):
        raise HTTPException(401, "Senha incorreta.",
                            headers={"WWW-Authenticate": 'Basic realm="Perguntas"'})


def mesma_origem(request: Request):
    """O navegador reenvia a senha do Basic sozinho; sem esta checagem, outro
    site conseguiria postar nos formulários do admin."""
    origem = request.headers.get("origin")
    if origem and urlsplit(origem).netloc != request.headers.get("host"):
        raise HTTPException(403, "Origem não permitida.")


ADMIN = [Depends(exigir_admin)]
ADMIN_POST = [Depends(exigir_admin), Depends(mesma_origem)]


@app.get("/admin", dependencies=ADMIN)
def admin(request: Request):
    with db.conectar() as con:
        total = db.total_respostas(con)
        perguntas = db.resultado(con)
    return pagina(request, "admin.html", url_resposta=url_resposta(request),
                  max_perguntas=db.MAX_PERGUNTAS, total=total, perguntas=perguntas,
                  texto_perguntas="\n".join(p["texto"] for p in perguntas))


@app.post("/admin/perguntas", dependencies=ADMIN_POST)
def admin_perguntas(texto: str = Form("")):
    linhas = [" ".join(linha.split())[:db.MAX_TEXTO] for linha in texto.splitlines()]
    textos = [linha for linha in linhas if linha][:db.MAX_PERGUNTAS]
    if textos:
        with db.conectar() as con:
            db.salvar_perguntas(con, textos)
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/limpar", dependencies=ADMIN_POST)
def admin_limpar():
    with db.conectar() as con:
        db.limpar(con)
    return RedirectResponse("/admin", status_code=303)
