from pathlib import Path
from nonebot import require
from nonebot.log import logger

require = require('nonebot_plugin_localstore')
from nonebot_plugin_localstore import get_data_dir

lagrange_path: Path = None
appsettings_path: Path = None
data_path: Path = get_data_dir('Lagrange/')
webui_path: Path = (Path(__file__).parent / 'webui')

logger.debug(F'数据目录为 {data_path}')


def update_file_paths():
    global appsettings_path, lagrange_path
    for file_path in data_path.rglob('*'):
        if file_path.name.startswith('Lagrange.OneBot'):
            lagrange_path = file_path.absolute()
        elif file_path.name == 'appsettings.json':
            appsettings_path = file_path.absolute()


update_file_paths()
