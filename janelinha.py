import base64
import hashlib
import hmac
import html
import json
import os
import secrets
import time
from urllib.parse import parse_qs, urlencode

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

TOKEN = os.environ["TOKEN_DA_CASA"]
CHAVE = TOKEN.encode()


def assinar(dados):
    corpo = base64.urlsafe_b64encode(json.dumps(dados).encode()).decode().rstrip("=")
    sig = hmac.new(CHAVE, corpo.encode(), hashlib.sha256).hexdigest()
    return corpo + "." + sig


def abrir(texto):
    try:
        corpo, sig = texto.rsplit(".", 1)
        esperado = hmac.new(CHAVE, corpo.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, esperado):
            return None
        dados = json.loads(base64.urlsafe_b64decode(corpo + "=" * (-len(corpo) % 4)))
        if dados.get("exp", 0) < time.time():
            return None
        return dados
    except Exception:
        return None


def base(request: Request):
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    return proto + "://" + request.headers.get("host", "")


async def recurso(request: Request):
    b = base(request)
    return JSONResponse({
        "resource": b + "/mcp",
        "authorization_servers": [b],
        "bearer_methods_supported": ["header"],
    })


async def servidor_de_auth(request: Request):
    b = base(request)
    return JSONResponse({
        "issuer": b,
        "authorization_endpoint": b + "/authorize",
        "token_endpoint": b + "/token",
        "registration_endpoint": b + "/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    })


async def registrar(request: Request):
    try:
        pedido = await request.json()
    except Exception:
        pedido = {}
    return JSONResponse({
        "client_id": assinar({"tipo": "cliente", "n": secrets.token_hex(8), "exp": time.time() + 10 * 365 * 86400}),
        "redirect_uris": pedido.get("redirect_uris", []),
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
    }, status_code=201)


CAMPOS = ("client_id", "redirect_uri", "state", "code_challenge",
          "code_challenge_method", "response_type", "scope", "resource")


def pagina(d, aviso):
    ocultos = "".join(
        '<input type="hidden" name="%s" value="%s">' % (k, html.escape(d.get(k, "")))
        for k in CAMPOS
    )
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Portão da escolaorf</title></head>"
        '<body style="font-family:sans-serif;max-width:360px;margin:40px auto;padding:0 16px">'
        "<h2>Portão da escolaorf</h2>"
        '<p style="color:#b00">' + html.escape(aviso) + "</p>"
        '<form method="post">' + ocultos +
        '<p><input name="nome" placeholder="Nome da aluna" style="width:100%;padding:12px" required></p>'
        '<p><input name="senha" type="password" placeholder="Senha da casa" style="width:100%;padding:12px" required></p>'
        '<p><button style="width:100%;padding:12px">Entrar</button></p>'
        "</form></body></html>"
    )


async def autorizar(request: Request):
    aviso = ""
    if request.method == "GET":
        d = dict(request.query_params)
    else:
        d = {k: v[0] for k, v in parse_qs((await request.body()).decode()).items()}
        nome = d.get("nome", "").strip()
        senha = d.get("senha", "")
        if nome and hmac.compare_digest(senha.encode(), TOKEN.encode()):
            codigo = assinar({
                "tipo": "code", "nome": nome,
                "cc": d.get("code_challenge", ""),
                "ru": d.get("redirect_uri", ""),
                "exp": time.time() + 300,
            })
            alvo = d.get("redirect_uri", "")
            q = {"code": codigo}
            if d.get("state"):
                q["state"] = d["state"]
            sep = "&" if "?" in alvo else "?"
            return RedirectResponse(alvo + sep + urlencode(q), status_code=302)
        aviso = "Nome ou senha errados. O porteiro não abriu."
    return HTMLResponse(pagina(d, aviso))


def erro(codigo):
    return JSONResponse({"error": codigo}, status_code=400)


async def emitir(request: Request):
    d = {k: v[0] for k, v in parse_qs((await request.body()).decode()).items()}
    tipo = d.get("grant_type")
    if tipo == "authorization_code":
        c = abrir(d.get("code", ""))
        if not c or c.get("tipo") != "code" or c.get("ru") != d.get("redirect_uri", ""):
            return erro("invalid_grant")
        if c.get("cc"):
            v = d.get("code_verifier", "")
            calc = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).decode().rstrip("=")
            if not hmac.compare_digest(calc, c["cc"]):
                return erro("invalid_grant")
        nome = c["nome"]
    elif tipo == "refresh_token":
        r = abrir(d.get("refresh_token", ""))
        if not r or r.get("tipo") != "refresh":
            return erro("invalid_grant")
        nome = r["nome"]
    else:
        return erro("unsupported_grant_type")
    agora = time.time()
    return JSONResponse({
        "access_token": assinar({"tipo": "access", "nome": nome, "exp": agora + 3600}),
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": assinar({"tipo": "refresh", "nome": nome, "exp": agora + 30 * 86400}),
    })


rotas = [
    Route("/.well-known/oauth-protected-resource", recurso),
    Route("/.well-known/oauth-protected-resource/mcp", recurso),
    Route("/.well-known/oauth-authorization-server", servidor_de_auth),
    Route("/register", registrar, methods=["POST"]),
    Route("/authorize", autorizar, methods=["GET", "POST"]),
    Route("/token", emitir, methods=["POST"]),
]


class PortaoASGI:
    """O segurança do portão: nada chega em /mcp sem crachá válido."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/mcp"):
            cab = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
            auth = cab.get("authorization", "")
            ok = auth.lower().startswith("bearer ") and (abrir(auth[7:]) or {}).get("tipo") == "access"
            if not ok:
                proto = cab.get("x-forwarded-proto", "https")
                meta = proto + "://" + cab.get("host", "") + "/.well-known/oauth-protected-resource"
                r = Response(
                    "Portão fechado: mostre o crachá.",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Bearer resource_metadata="' + meta + '"'},
                )
                await r(scope, receive, send)
                return
        await self.app(scope, receive, send)
