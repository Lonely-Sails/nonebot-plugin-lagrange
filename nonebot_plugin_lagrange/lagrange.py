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
        lagrange_config['QrCode']['ConsoleCompatibilityMode'] = True
        lagrange_config['Implementations'][0]['Port'] = self.config.port
        lagrange_config['Implementations'][0]['Host'] = str(self.config.host)
        lagrange_config['Implementations'][0]['AccessToken'] = self.config.onebot_access_token
        if not lagrange_config['SignServerUrl']:
            logger.info('检测到未设置签名服务器地址！将使用配置的签名地址。')
            lagrange_config['SignServerUrl'] = self.config.lagrange_sign_server_url
        with config_path.open('w', encoding='Utf-8') as file:
            dump(lagrange_config, file)
            self.log('SUCCESS', 'Lagrange.Onebot 配置文件更新成功！')
            return True

    def log(self, level: str, content: str):
        content = F'[{self.name}] {content}'
        logger.log(level, content)

    async def stop(self):
        if self.task is not None:
            try:
                self.task.terminate()
            except ProcessLookupError:
                logger.info(F'Lagrange.Onebot 进程 {self.task} 已退出！')
                self.task = None
                return await self.deal_lagrange_log('§dialog§Lagrange.OneBot 已经退出！')
            checker_task = asyncio.create_task(self.checker())
            await self.task.wait()
            checker_task.cancel()
            self.log_task.cancel()
            self.error_task.cancel()
            self.task = None
            self.log('INFO', 'Lagrange.Onebot 已退出！如若没有正常使用，请检查日志。')
            await self.deal_lagrange_log('§dialog§Lagrange.OneBot 已退出！')

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
            await self.deal_lagrange_log('§dialog§Lagrange.OneBot 未响应！已强制关闭。')

    async def listen_log(self):
        async for line in self.task.stdout:
            line = line.decode('Utf-8').rstrip()
            await self.deal_lagrange_log(line)
            if line[0] in ('█', '▀'):
                self.log('INFO', line)
                continue
            elif log_info := parse_log_level(line):
                log_class, log_level, message = log_info
                if log_level == 'WARNING':
                    self.log('WARNING', message)
                    continue
                elif log_level == 'FATAL':
                    self.log('ERROR', message)
                    if '45' in message and 'Login failed' in message:
                        self.log('WARNING', '检测到协议错误导致登录失败！请尝试更新以解决此问题。')
                        await self.deal_lagrange_log('§dialog§检测到登录失败！请尝试更新以解决此问题。')
                    continue
                self.log('DEBUG', message)
            if 'Lagrange.OneBot Implementation has stopped' in line:
                break
        await self.deal_lagrange_log('§dialog§Lagrange.OneBot 已退出！')
        self.task = None

    async def listen_error(self):
        async for line in self.task.stderr:
            line = line.decode('Utf-8').rstrip()
            self.log('ERROR', line)
            await self.deal_lagrange_log('§error§' + line)

    async def deal_lagrange_log(self, log: str):
        if len(self.cache) > self.config.lagrange_max_cache_log:
            self.cache.pop(0)
        self.cache.append(log)
        for connection in self.connections:
            await connection.send(log)
