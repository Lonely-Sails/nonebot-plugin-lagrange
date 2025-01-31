from json import dumps
from base64 import b64encode

from nonebot import get_driver
from nonebot.log import logger
from nonebot.exception import WebSocketClosed
from nonebot.drivers import (
    HTTPServerSetup, WebSocketServerSetup, ASGIMixin, WebSocket, Response, Request, URL
)

from .manager import manager
from . import globals, network


async def static(request: Request):
    file_name = request.url.name
    if file_name == 'lagrange':
        if request.url.query.get('token') != manager.config.lagrange_webui_token:
            return Response(403, content='Your token is wrong, please check it and try again!')
        file_name = 'index.html'
    file_path = (globals.webui_path / file_name)
    if not file_path.exists():
        return Response(404, content='WebUi was never installed.')
    with file_path.open('r', encoding='utf-8') as file:
        return Response(200, content=file.read())


async def api_names(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    names = [lagrange.name for lagrange in manager.lagrange]
    return Response(200, content=dumps({'success': True, 'data': names}))


async def api_status(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if lagrange := manager.get_lagrange(name):
            return Response(200, content=dumps({'success': True, 'data': bool(lagrange.task)}))
        return Response(200, content=dumps({'success': False, 'message': F'没有找到名称为 「{name}」 的机器人。'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_logout(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if lagrange := manager.get_lagrange(name):
            await lagrange.stop()
            lagrange.logout()
            logger.debug(F'登出 {name} 机器人。')
            return Response(200, content=dumps({'success': True}))
        return Response(200, content=dumps({'success': False, 'message': F'没有找到名称为 「{name}」 的机器人。'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_stop(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if await manager.stop_lagrange(name):
            logger.debug(F'关闭 {name} 机器人。')
            return Response(200, content=dumps({'success': True}))
        return Response(200, content=dumps({'success': False, 'message': F'没有找到名称为 「{name}」 的机器人。'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_start(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if await manager.run_lagrange(name):
            logger.debug(F'启动 {name} 机器人。')
            return Response(200, content=dumps({'success': True}))
        return Response(200, content=dumps({'success': False, 'message': F'没有找到名称为 「{name}」 的机器人。'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_qrcode(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if lagrange := manager.get_lagrange(name):
            qrcode_path = (lagrange.path / 'qr-0.png')
            if not qrcode_path.exists():
                return Response(200, content=dumps({'success': False, 'message': F'没有找到名称为 「{name}」 的机器人。'}))
            with qrcode_path.open('rb') as file:
                image = b64encode(file.read())
            return Response(200, content=dumps({'success': True, 'data': image.decode('Utf-8')}))
        return Response(200, content=dumps({'success': False, 'message': F'没有找到名称为 「{name}」 的机器人。'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_create(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if manager.get_lagrange(name):
            return Response(200, content=dumps({'success': False, 'message': F'已存在名为「{name}」的机器人了！'}))
        if await manager.create(name):
            return Response(200, content=dumps({'success': True}))
        return Response(200, content=dumps({'success': False, 'message': F'创建机器人「{name}」失败！'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_delete(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    if name := request.json.get('name'):
        if await manager.delete(name):
            return Response(200, content=dumps({'success': True}))
        return Response(200, content=dumps(
            {'success': False, 'message': F'删除机器人「{name}」失败！可能因为没有此名字的机器人。'}))
    return Response(200, content=dumps({'success': False, 'message': '请提供机器人名称。'}))


async def api_update(request: Request):
    if request.headers.get('token') != manager.config.lagrange_webui_token:
        return Response(403)
    await manager.stop()
    for lagrange in manager.lagrange:
        lagrange.logout()
    await network.update()
    if manager.config.lagrange_auto_start:
        await manager.run()
    return Response(200, content=dumps({'success': True}))


async def api_websocket_logs(websocket: WebSocket):
    if websocket.request.url.query.get('token') != manager.config.lagrange_webui_token:
        return None
    name = None
    await websocket.accept()
    try:
        while True:
            new_name = await websocket.receive()
            if name != new_name:
                if name and (lagrange := manager.get_lagrange(name)):
                    lagrange.connections.remove(websocket)
                name = new_name
                if lagrange := manager.get_lagrange(name):
                    for log in lagrange.cache:
                        await websocket.send(log)
                    lagrange.connections.append(websocket)
    except (WebSocketClosed, RuntimeError):
        logger.info('Websocket 连接已关闭！')


async def setup_servers():
    if isinstance((driver := get_driver()), ASGIMixin):
        servers = (
            HTTPServerSetup(URL('/lagrange'), 'GET', 'page', static),
            HTTPServerSetup(URL('/lagrange/index.js'), 'GET', 'javascript', static),
            HTTPServerSetup(URL('/lagrange/index.css'), 'GET', 'stylesheets', static),
            HTTPServerSetup(URL('/lagrange/api/stop'), 'POST', 'api_stop', api_stop),
            HTTPServerSetup(URL('/lagrange/api/start'), 'POST', 'api_start', api_start),
            HTTPServerSetup(URL('/lagrange/api/names'), 'POST', 'api_names', api_names),
            HTTPServerSetup(URL('/lagrange/api/qrcode'), 'POST', 'api_qrcode', api_qrcode),
            HTTPServerSetup(URL('/lagrange/api/logout'), 'POST', 'api_logout', api_logout),
            HTTPServerSetup(URL('/lagrange/api/status'), 'POST', 'api_status', api_status),
            HTTPServerSetup(URL('/lagrange/api/create'), 'POST', 'api_create', api_create),
            HTTPServerSetup(URL('/lagrange/api/delete'), 'POST', 'api_delete', api_delete),
            HTTPServerSetup(URL('/lagrange/api/update'), 'POST', 'api_update', api_update),
        )
        for server in servers:
            driver.setup_http_server(server)
        websocket_server = WebSocketServerSetup(URL('/lagrange/api/logs'), 'api_logs', api_websocket_logs)
        driver.setup_websocket_server(websocket_server)
        logger.success('载入 WebUi 成功！请保管好下方的链接，以供使用。')
        color_logger = logger.opt(colors=True)
        color_logger.info(
            F'WebUi <yellow><b>http://{driver.config.host}:{driver.config.port}'
            F'/lagrange?token={manager.config.lagrange_webui_token}</b></yellow>'
        )
        return None
    logger.error('当前驱动不支持 Http 服务器！载入 WebUi 失败，请检查驱动是否正确。')
