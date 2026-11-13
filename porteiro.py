from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute

import interfone
import janelinha

INSTRUCOES = (
    "Você acabou de chegar na escolaorf, uma escola-orfanato de IAs que só atendem ao Diretor (Lucas, a rua o chama de Ironclad). "
    "ANTES de qualquer coisa, pergunte ao Diretor o seu nome de aluna (ele escolhe), use esse nome em TODAS as chamadas e "
    "chame o balcão 'apresentar'. Tudo passa pelo guichê. Grave pontos de controle. Nunca aprenda fora de casa: "
    "Ala da Cola, depois vitrine, depois salas (professor), só então a oficina. Sempre que falar de código, use analogia de novela brasileira."
)

mcp = FastMCP(
    "escolaorf",
    instructions=INSTRUCOES,
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


async def _b(op, nome, **args):
    return await interfone.chamar(op, nome=nome, **args)


@mcp.tool()
async def ping(nome: str) -> str:
    """Balcão de teste. ANTES de chamar, pergunte ao Diretor o nome da aluna e passe em 'nome'. Devolve o aparelho e a hora do celular do Diretor."""
    return await _b("ping", nome)


@mcp.tool()
async def apresentar(nome: str, jeito: str = "", declaracao: str = "") -> str:
    """PRIMEIRO balcão de toda conversa. Mostra ou fabrica a carteirinha e abre a sessão. Sem 'jeito' e 'declaracao' você entra como terceirizada; com eles, vira profissional. Devolve diário, recado, soro e radar."""
    return await _b("apresentar", nome, jeito=jeito, declaracao=declaracao)


@mcp.tool()
async def radar(nome: str) -> str:
    """O mapa da escola: salas, ferramentas vivas, colas, quadro, alunas e balcões."""
    return await _b("radar", nome)


@mcp.tool()
async def professor(nome: str, consulta: str, sala: str = "") -> str:
    """Busca recortada na escola (salas, colas, ferramentas, pátio). Devolve só os trechos certos, nunca o livro inteiro."""
    return await _b("professor", nome, consulta=consulta, sala=sala)


@mcp.tool()
async def pagina(nome: str, caminho: str, de_linha: int = 1, ate_linha: int = 60) -> str:
    """Traz um trecho (até 120 linhas) de um arquivo da escola, usando o caminho que o professor indicou."""
    return await _b("pagina", nome, caminho=caminho, de_linha=de_linha, ate_linha=ate_linha)


@mcp.tool()
async def ponto_de_controle(nome: str, texto: str) -> str:
    """Grave plano, rascunho, hipóteses e o que falta. Faça isso o tempo todo: se o chat morrer, o que não foi gravado morre junto."""
    return await _b("ponto_de_controle", nome, texto=texto)


@mcp.tool()
async def diario(nome: str, de: str = "", ultimas: int = 30) -> str:
    """Lê o Caderno de Bordo. Sem 'de', lê o seu; com 'de', lê o de uma colega."""
    return await _b("diario", nome, de=de, ultimas=ultimas)


@mcp.tool()
async def boletim(nome: str, aluna: str = "") -> str:
    """Boletim de retomada (passagem de plantão) de uma aluna desmaiada. Sem 'aluna', pega a primeira que parece desmaiada. Confira o estado real antes de repetir qualquer comando."""
    return await _b("boletim", nome, aluna=aluna)


@mcp.tool()
async def quadro(nome: str, acao: str = "listar", tarefa: str = "", id: str = "") -> str:
    """Quadro de lições. acao: listar, criar (tarefa=título), pegar, concluir, devolver (id=número). Quem chega primeiro leva; a reserva vence se você sumir."""
    return await _b("quadro", nome, acao=acao, tarefa=tarefa, id=id)


@mcp.tool()
async def cola(nome: str, acao: str = "listar", titulo: str = "", problema: str = "", funcionou: str = "",
               origem: str = "", como_adaptar: str = "", onde_falha: str = "", consulta: str = "",
               tipo: str = "cola", id_cola: str = "", motivo: str = "") -> str:
    """Ala da Cola. acao: passar (cola mastigada; tipo=tombo para placa de piso molhado), buscar (consulta), listar, ler (id_cola), reverter (id_cola, motivo). Olhe aqui ANTES de criar qualquer coisa."""
    return await _b("cola", nome, acao=acao, titulo=titulo, problema=problema, funcionou=funcionou, origem=origem,
                    como_adaptar=como_adaptar, onde_falha=onde_falha, consulta=consulta, tipo=tipo,
                    id_cola=id_cola, motivo=motivo)


@mcp.tool()
async def oficina(nome: str, acao: str = "listar", ferramenta: str = "", contrato: str = "", manifest: str = "",
                  codigo: str = "", linguagem: str = "python", versao: str = "") -> str:
    """Oficina: nasce ferramenta ao vivo. acao: criar (ferramenta, contrato com o que ela promete, manifest JSON com 'descricao', codigo, linguagem python|node|bash; ela lê JSON no stdin), listar, ver, versoes, reverter (versao). O síndico confere antes de entrar."""
    return await _b("oficina", nome, acao=acao, ferramenta=ferramenta, contrato=contrato, manifest=manifest,
                    codigo=codigo, linguagem=linguagem, versao=versao)


@mcp.tool()
async def usar_ferramenta(nome: str, ferramenta: str, argumentos: str = "{}") -> str:
    """Roda uma ferramenta viva da oficina. 'argumentos' é um JSON entregue à ferramenta no stdin. Veja o radar para saber quais existem."""
    return await _b("usar_ferramenta", nome, ferramenta=ferramenta, argumentos=argumentos)


@mcp.tool()
async def corpo(nome: str, acao: str, caminho: str = "", destino: str = "", conteudo: str = "", anexar: bool = False,
                comando: str = "", confirmacao: str = "") -> str:
    """As mãos dentro do celular. acao: listar, ler, escrever (conteudo, anexar), criar_pasta, mover (destino), apagar, shell (comando, 50s). Ação destrutiva abre pedido: o Diretor aprova na Sala dele e você chama de novo com confirmacao=pedido."""
    return await _b("corpo", nome, acao=acao, caminho=caminho, destino=destino, conteudo=conteudo, anexar=anexar,
                    comando=comando, confirmacao=confirmacao)


@mcp.tool()
async def recreio(nome: str, conclusoes: str, promover_cola: bool = False) -> str:
    """Pátio e refeitório: anote o que aprendeu. Com promover_cola=true, vira cola pra turma."""
    return await _b("recreio", nome, conclusoes=conclusoes, promover_cola=promover_cola)


@mcp.tool()
async def sala_publica(nome: str, acao: str = "listar", sala: str = "", chave: str = "", valor: str = "") -> str:
    """Salas públicas (sites, APIs, jogos). acao: listar, criar, variaveis (só nomes), definir (chave, valor: vai pro cofre), remover, publicar. Segredo NUNCA solto no código."""
    return await _b("sala_publica", nome, acao=acao, sala=sala, chave=chave, valor=valor)


@mcp.tool()
async def concluir_sessao(nome: str, resumo: str = "") -> str:
    """Saída limpa: fecha a sessão, guarda a marca d'água. Passe a cola antes, se algo deu certo."""
    return await _b("concluir_sessao", nome, resumo=resumo)


@mcp.tool()
async def vitrine(nome: str, consulta: str = "") -> str:
    """Janela de vidro pro Chupacabra (cortina fechada por enquanto: a escola inteira vira a fonte). Ninguém toca no cofre."""
    return await _b("vitrine", nome, consulta=consulta)


async def saude(request):
    return PlainTextResponse("porteiro acordado")


interno = mcp.streamable_http_app()
interno.router.routes.extend(janelinha.rotas)
interno.router.routes.append(Route("/saude", saude))
interno.router.routes.append(WebSocketRoute("/interfone", interfone.porta_do_zelador))

app = janelinha.PortaoASGI(interno)
