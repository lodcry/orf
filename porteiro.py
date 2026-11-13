from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute

import interfone
import janelinha

mcp = FastMCP(
    "escolaorf",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.tool()
async def ping() -> str:
    """Balcão de teste da escolaorf. Pergunta ao zelador o nome do aparelho e a hora do celular do Diretor. Se a resposta vier do celular, a ponte existe."""
    return await interfone.chamar("ping")


async def saude(request):
    return PlainTextResponse("porteiro acordado")


interno = mcp.streamable_http_app()
interno.router.routes.extend(janelinha.rotas)
interno.router.routes.append(Route("/saude", saude))
interno.router.routes.append(WebSocketRoute("/interfone", interfone.porta_do_zelador))

from starlette.middleware.cors import CORSMiddleware

app = CORSMiddleware(
    janelinha.PortaoASGI(interno),
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["WWW-Authenticate", "Mcp-Session-Id"],
)
