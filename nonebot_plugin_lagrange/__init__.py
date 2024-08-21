import nonebot
from nonebot.plugin import PluginMetadata

from .config import Config
from .manager import manager
from .globals import update_file_paths
from .servers import setup_servers

__plugin_meta__ = PluginMetadata(
    name='lagrange',
    description='A simple Lagrange.OneBot manager plugin.',
    usage='Lagrange.OneBot manager plugin. Can use command to manage it.',
    type='application',
    homepage='https://www.github.com/Lonely-Sails/nonebot-plugin-lagrange',
    config=Config,
    supported_adapters={'~onebot.v11'},
)

driver = nonebot.get_driver()

status_matcher = nonebot.on_command('拉格兰状态', aliases={'状态'})


@driver.on_startup
async def startup():
    if manager.config.lagrange_auto_start:
        await manager.run()
    if manager.config.lagrange_webui:
        await setup_servers()


@driver.on_shutdown
async def shutdown():
    await manager.stop()


@status_matcher.handle()
async def status():
    reply = []
    for lagrange in manager.lagrange:
        if lagrange.task is None:
            reply.append(F'{lagrange.name} -> 关闭')
            continue
        reply.append(F'{lagrange.name} -> 开启')
    await status_matcher.finish('\n'.join(reply))
