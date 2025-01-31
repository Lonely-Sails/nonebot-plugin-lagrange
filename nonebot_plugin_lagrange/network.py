import tarfile
from zipfile import ZipFile
from io import BytesIO
from httpx import AsyncClient
from typing import Literal

from nonebot.log import logger

from . import globals
from .utils import generate_default_settings, parse_platform


def extract_lagrange(file: BytesIO, file_type: Literal['tar', 'zip']):
    def extract_tar():
        with tarfile.open(fileobj=file) as tar_file:
            for member in tar_file.getmembers():
                if not member.isfile():
                    continue
                with tar_file.extractfile(member) as lagrange_file:
                    with open(globals.data_path / 'Lagrange.OneBot', 'wb') as target_file:
                        target_file.write(lagrange_file.read())
                        return True

    def extract_zip():
        with ZipFile(file) as zip_file:
            for name in zip_file.namelist():
                if name.endswith('Lagrange.OneBot.exe'):
                    with open(globals.data_path / 'Lagrange.OneBot.exe', 'wb') as target_file:
                        target_file.write(zip_file.read(name))
                        return True

    try:
        if file_type == 'tar':
            return extract_tar()
        elif file_type == 'zip':
            return extract_zip()
    except Exception as error:
        logger.error(F'Lagrange.Onebot 解压失败！错误信息 {error.args}')
    return False


async def update():
    logger.info('Lagrange.Onebot 正在更新……')
    if globals.lagrange_path is not None:
        globals.lagrange_path.unlink()
    if globals.appsettings_path is not None:
        globals.appsettings_path.unlink()
    globals.lagrange_path = None
    globals.appsettings_path = None
    return await install()


async def install():
    if globals.lagrange_path is not None:
        logger.warning('检测到 Lagrange.Onebot 已安装，无需再次安装！')
        return True
    system, architecture = parse_platform()
    logger.info(F'检测到当前的系统架构为 {system} {architecture} 正在下载对应的安装包……')
    file_foramt = 'zip' if system == 'win' else 'tar.gz'
    download_url = (
        'https://github.com/LagrangeDev/Lagrange.Core/releases/download/'
        F'nightly/Lagrange.OneBot_{system}-{architecture}_net9.0_SelfContained.{file_foramt}'
    )
    response = await download('https://www.ghproxy.cn/' + download_url)
    if not response:
        logger.error('使用代理下载失败！正在尝试使用直链下载……')
        response = await download(download_url)
    if response:
        logger.success(F'Lagrange.Onebot 下载成功！正在安装……')
        if extract_lagrange(response, 'zip' if system == 'win' else 'tar'):
            generate_default_settings()
            globals.update_file_paths()
            logger.success('Lagrange.Onebot 安装成功！')
            return True
    logger.error('Lagrange.Onebot 安装失败！请尝试使用代理后再试。')
    return False


async def download(url: str):
    download_bytes = BytesIO()
    logger.debug(F'正在从 {url} 下载文件……')
    async with AsyncClient() as client:
        try:
            async with client.stream('GET', url) as stream:
                if stream.status_code != 200:
                    return False
                async for chunk in stream.aiter_bytes():
                    download_bytes.write(chunk)
                download_bytes.seek(0)
                return download_bytes
        except Exception as error:
            logger.error(F'下载失败！错误信息 {error.args}')
            return False
