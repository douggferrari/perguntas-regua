"""SQLite em DATA_DIR (no Railway, o volume montado em /data)."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
DB_PATH = DATA_DIR / "perguntas.db"

MAX_PERGUNTAS = 10
MAX_TEXTO = 200

PERGUNTAS_PADRAO = (
    "Com todo esse cenário, a Credsystem está entregando aquilo que gera valor?",
    "Conseguimos ter visibilidade de quanto tempo levamos para colocar um projeto em produção?",
    "Podemos assumir compromissos de maneira confiável?",
    "Estamos entregando com qualidade?",
    "Temos uma boa cultura de convívio e colaboração?",
)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS perguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ordem INTEGER NOT NULL,
    texto TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa TEXT NOT NULL UNIQUE,  -- id do cookie do navegador: uma resposta por pessoa
    criada_em TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Posição que a pessoa marcou na régua de cada pergunta: 0 = Não, 100 = Sim.
CREATE TABLE IF NOT EXISTS valores (
    resposta INTEGER NOT NULL REFERENCES respostas (id) ON DELETE CASCADE,
    pergunta INTEGER NOT NULL REFERENCES perguntas (id) ON DELETE CASCADE,
    valor INTEGER NOT NULL CHECK (valor BETWEEN 0 AND 100),
    PRIMARY KEY (resposta, pergunta)
);
CREATE INDEX IF NOT EXISTS ix_valores_pergunta ON valores (pergunta);
"""


@contextmanager
def conectar():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("PRAGMA foreign_keys = ON")  # vale por conexão; sem ele o CASCADE não roda
    try:
        with con:  # commit no fim, rollback se der erro
            yield con
    finally:
        con.close()


def criar_esquema():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with conectar() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(ESQUEMA)
        # As perguntas padrão só entram no primeiro boot; depois quem manda é o /admin.
        if not con.execute("SELECT 1 FROM perguntas LIMIT 1").fetchone():
            salvar_perguntas(con, PERGUNTAS_PADRAO)


def perguntas(con) -> list[dict]:
    return [
        {"id": id_, "texto": texto}
        for id_, texto in con.execute("SELECT id, texto FROM perguntas ORDER BY ordem, id")
    ]


def salvar_perguntas(con, textos):
    """Troca as perguntas, uma por posição. Editar o texto de uma posição mantém
    as respostas dela; posições a mais entram vazias; as que sumirem levam as
    respostas junto (CASCADE)."""
    atuais = [p["id"] for p in perguntas(con)]
    for ordem, texto in enumerate(textos):
        if ordem < len(atuais):
            con.execute("UPDATE perguntas SET texto = ?, ordem = ? WHERE id = ?",
                        (texto, ordem, atuais[ordem]))
        else:
            con.execute("INSERT INTO perguntas (ordem, texto) VALUES (?, ?)", (ordem, texto))
    for id_ in atuais[len(textos):]:
        con.execute("DELETE FROM perguntas WHERE id = ?", (id_,))


def adicionar(con, pessoa: str, valores: dict[int, int]) -> bool:
    """Grava as respostas da pessoa; False se ela já tinha respondido. O UNIQUE
    em `pessoa` segura também o duplo toque no botão (dois POSTs juntos)."""
    cur = con.execute(
        "INSERT INTO respostas (pessoa) VALUES (?) ON CONFLICT (pessoa) DO NOTHING", (pessoa,))
    if cur.rowcount != 1:
        return False
    con.executemany(
        "INSERT INTO valores (resposta, pergunta, valor) VALUES (?, ?, ?)",
        [(cur.lastrowid, pergunta, valor) for pergunta, valor in valores.items()],
    )
    return True


def respostas_de(con, pessoa: str) -> list[dict] | None:
    """O que a pessoa marcou, na ordem das perguntas; None se ainda não respondeu."""
    linha = con.execute("SELECT id FROM respostas WHERE pessoa = ?", (pessoa,)).fetchone()
    if not linha:
        return None
    return [
        {"texto": texto, "valor": valor}
        for texto, valor in con.execute(
            "SELECT p.texto, v.valor FROM valores v JOIN perguntas p ON p.id = v.pergunta"
            " WHERE v.resposta = ? ORDER BY p.ordem, p.id",
            (linha[0],),
        )
    ]


def total_respostas(con) -> int:
    return con.execute("SELECT COUNT(*) FROM respostas").fetchone()[0]


def resultado(con) -> list[dict]:
    """Média de cada pergunta (0 a 100) e quantas pessoas a responderam."""
    return [
        {"id": id_, "texto": texto, "media": None if media is None else round(media, 1), "n": n}
        for id_, texto, media, n in con.execute(
            "SELECT p.id, p.texto, AVG(v.valor), COUNT(v.valor) FROM perguntas p"
            " LEFT JOIN valores v ON v.pergunta = p.id"
            " GROUP BY p.id ORDER BY p.ordem, p.id"
        )
    ]


def limpar(con):
    """Rodada nova: apaga tudo e libera todo mundo para responder de novo."""
    con.execute("DELETE FROM respostas")
