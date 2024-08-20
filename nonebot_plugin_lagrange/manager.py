import asyncio

from nonebot.log import logger
from nonebot.plugin import get_plugin_config

from . import globals
from .config import Config
from .lagrange import Lagrange
from .network import install
from .utils import generate_token


class Manager:
    lagrange: list = []

    config: Config = None

    def __init__(self):
        self.config = get_plugin_config(Config)
        if self.config.lagrange_webui:
            self.update_token()
        for lagrange_name in self.config.lagrange_path.rglob('*'):
            if lagrange_name.is_dir():
                self.lagrange.append(Lagrange(self.config, lagrange_name.name))
        if globals.lagrange_path and self.config.lagrange_auto_start:
            logger.info('Lagrange.Onebot 已经安装，正在启动……')
            if not self.lagrange: asyncio.run(self.create('Default'))
        elif (not globals.lagrange_path) and self.config.lagrange_auto_install:
            logger.info('Lagrange.Onebot 未安装，正在安装……')
            asyncio.run(install())

    def update_token(self):
        if not self.config.lagrange_path.exists():
            self.config.lagrange_path.mkdir()
        if not self.config.lagrange_webui_token:
            token_path = (self.config.lagrange_path / 'token.bin')
            if not token_path.exists():
                self.config.lagrange_webui_token = generate_token()
                with token_path.open('w', encoding='Utf-8') as file:
                    file.write(self.config.lagrange_webui_token)
                return None
            with token_path.open('r', encoding='Utf-8') as file:
                self.config.lagrange_webui_token = file.read()

    async def create(self, lagrange_name: str, auto_run: bool = True):
        if not globals.lagrange_path:
            logger.error('Lagrange.Onebot 未安装，无法创建 Lagrange')
            return False
        elif lagrange_name in (lagrange.name for lagrange in self.lagrange):
            logger.warning(F'Lagrange {lagrange_name} 已存在，无法重复创建')
            return False
        lagrange = Lagrange(self.config, lagrange_name)
        self.lagrange.append(lagrange)
        if auto_run is True:
            await asyncio.create_task(lagrange.run())
        return True

    async def delete(self, lagrange_name: str):
        if lagrange := self.get_lagrange(lagrange_name):
            await lagrange.stop()
            for file_path in lagrange.path.rglob('*'):
                file_path.unlink()
            lagrange.path.rmdir()
            self.lagrange.remove(lagrange)
            return True

    async def run(self):
        for lagrange in self.lagrange:
            await asyncio.create_task(lagrange.run())
            await asyncio.sleep(5)

    async def run_lagrange(self, lagrange_name: str):
        if lagrange := self.get_lagrange(lagrange_name):
            await asyncio.create_task(lagrange.run())
            return True
        return False

    async def stop(self):
        for lagrange in self.lagrange:
            try: await lagrange.stop()
            except Exception as error: pass

    async def stop_lagrange(self, lagrange_name: str):
        if lagrange := self.get_lagrange(lagrange_name):
            await lagrange.stop()
            return True

    def get_lagrange(self, lagrange_name: str):
        for lagrange in self.lagrange:
            if lagrange.name == lagrange_name:
                return lagrange


manager = Manager()
