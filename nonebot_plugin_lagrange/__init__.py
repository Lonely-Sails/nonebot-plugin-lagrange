import nonebot
from nonebot import on_command
from nonebot.permission import SUPERUSER
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
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。

    homepage='https://www.github.com/Lonely-Sails/nonebot-plugin-lagrange',
    # 发布必填。

    config=Config,
    # 插件配置项类，如无需配置可不填写。

    supported_adapters={'~onebot.v11'},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

driver = nonebot.get_driver()


@driver.on_startup
async def startup():
    if manager.config.lagrange_auto_start:
        await manager.run()
    if manager.config.lagrange_webui:
        await setup_servers()


@driver.on_shutdown
async def shutdown():
    await manager.stop()
