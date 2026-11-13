import asyncio
import hmac
import json
import os
import uuid

from starlette.websockets import WebSocket, WebSocketDisconnect

TOKEN = os.environ["TOKEN_DA_CASA"]
zelador = None
pendentes = {}


async def chamar(op, **args):
    if zelador is None:
        return "Escola fechada: o zelador ainda não abriu. (Termux desligado ou sem conexão com o Render.)"
    rid = uuid.uuid4().hex
    fut = asyncio.get_running_loop().create_future()
    pendentes[rid] = fut
    try:
        await zelador.send_text(json.dumps({"id": rid, "op": op, "args": args}))
        return await asyncio.wait_for(fut, 60)
    except asyncio.TimeoutError:
        return "O zelador não respondeu a tempo. (timeout de 60s)"
    except Exception as e:
        return "O interfone falhou. (" + str(e) + ")"
    finally:
        pendentes.pop(rid, None)


async def porta_do_zelador(ws: WebSocket):
    global zelador
    await ws.accept()
    try:
        primeira = json.loads(await asyncio.wait_for(ws.receive_text(), 10))
        if not hmac.compare_digest(str(primeira.get("token", "")).encode(), TOKEN.encode()):
            await ws.close(code=1008)
            return
    except Exception:
        await ws.close(code=1008)
        return
    zelador = ws
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            fut = pendentes.get(msg.get("id"))
            if fut and not fut.done():
                fut.set_result(msg.get("resultado"))
    except WebSocketDisconnect:
        pass
    finally:
        if zelador is ws:
            zelador = None
