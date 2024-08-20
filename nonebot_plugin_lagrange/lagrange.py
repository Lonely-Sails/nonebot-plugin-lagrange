import asyncio
from asyncio import Task
from asyncio.subprocess import Process, PIPE
from pathlib import Path
from json import dump, load

from nonebot.log import logger

from . import globals
from .utils import parse_log_level
from .config import Config
from .network import generate_default_settings


class Lagrange:
    name: str = None
    cache: list = None
    connections: list = None

    path: Path = None
    task: Process = None
    config: Config = None

    log_task: Task = None
    error_task: Task = None

    def __init__(self, config: Config, name: str):
        self.cache = []
        self.connections = []
        self.config, self.name = config, name
        self.path = (self.config.lagrange_path / name)

    def rename(self, name: str):
        self.name = name
        self.path = self.path.rename(name)

    def logout(self):
        if self.task is None:
            for file_path in self.path.rglob('*'):
                if file_path.name != 'appsettings.json':
                    file_path.unlink()

    def update_config(self):
        if not self.path.exists():
            self.path.mkdir()
        config_path = (self.path / 'appsettings.json')
        if globals.appsettings_path is None:
            generate_default_settings()
            globals.update_file_paths()
        with globals.appsettings_path.open('r', encoding='Utf-8') as file:
            lagrange_config = load(file)
        lagrange_config['Implementations'][0]['Port'] = self.config.port
        lagrange_config['Implementations'][0]['Host'] = str(self.config.host)
        lagrange_config['Implementations'][0]['AccessToken'] = self.config.onebot_access_token
        with config_path.open('w', encoding='Utf-8') as file:
            dump(lagrange_config, file)
            self.log('SUCCESS', 'Lagrange.Onebot 配置文件更新成功！')
            return True

    def log(self, level: str, content: str):
        content = F'[{self.name}] {content}'
        logger.log(level, content)

    async def stop(self):
        if self.task is not None:
            self.task.terminate()
            checker_task = asyncio.create_task(self.checker())
            await self.task.wait()
            checker_task.cancel()
            self.log_task.cancel()
            self.error_task.cancel()
            self.task = None
            self.log('INFO', 'Lagrange.Onebot 已退出！如若没有正常使用，请检查日志。')

    async def run(self):
        self.cache.clear()
        self.update_config()
        self.task = await asyncio.create_subprocess_exec(
            str(globals.lagrange_path), stdout=PIPE, stderr=PIPE, cwd=self.path
        )
        self.log_task = asyncio.create_task(self.listen_log())
        self.error_task = asyncio.create_task(self.listen_error())
        self.log('SUCCESS', 'Lagrange.Onebot 启动成功！请扫描目录下的图片或控制台中的二维码登录。')

    async def checker(self):
        await asyncio.sleep(10)
        if self.task is not None:
            logger.warning(F'Lagrange.Onebot 进程 {self.task} 未响应！正在强制关闭。')
            self.task.kill()

    async def listen_log(self):
        async for line in self.task.stdout:
            line = line.decode('Utf-8').strip()
            await self.deal_lagrange_log(line)
            if line[0] in ('█', '▀'):
                self.log('INFO', line)
                continue
            elif log_level := parse_log_level(line):
                if log_level == 'WARNING':
                    self.log('WARNING', line)
                    continue
                self.log('DEBUG', line)
            if line == 'Lagrange.OneBot Implementation has stopped':
                break

    async def listen_error(self):
        async for line in self.task.stderr:
            self.log('ERROR', line)
            line = line.decode('Utf-8').strip()
            await self.deal_lagrange_log('§error§' + line)

    async def deal_lagrange_log(self, log: str):
        if len(self.cache) > self.config.lagrange_max_cache_log:
            self.cache.pop(0)
        self.cache.append(log)
        for connection in self.connections:
            await connection.send(log)
