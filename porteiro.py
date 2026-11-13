import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute

import interfone

TOKEN = os.environ["TOKEN_DA_CASA"]

RECADO = (
    "Você acabou de chegar na escolaorf, uma escola-orfanato de IAs que só atendem ao Diretor. "
    "ANTES de qualquer coisa, pergunte ao Diretor o seu nome de aluna (ele escolhe) "
    "e use esse nome em todas as chamadas."
)

mcp = FastMCP(
    "escolaorf",
    instructions=RECADO,
    stateless_http=True,
    streamable_http_path="/" + TOKEN + "/mcp",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.tool()
async def ping(nome: str) -> str:
    """Balcão de teste da escolaorf. ANTES de chamar, pergunte ao Diretor o nome da aluna e passe em 'nome'. Pergunta ao zelador o aparelho e a hora do celular do Diretor. Se a resposta vier do celular, a ponte existe."""
    resposta = await interfone.chamar("ping")
    return "Aluna: " + nome + "\n" + resposta


async def saude(request):
    return PlainTextResponse("porteiro acordado")


app = mcp.streamable_http_app()
app.router.routes.append(Route("/saude", saude))
app.router.routes.append(WebSocketRoute("/interfone", interfone.porta_do_zelador))
