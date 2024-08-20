import tarfile
from io import BytesIO
from httpx import AsyncClient

from nonebot.log import logger

from . import globals
from .utils import generate_default_settings, parse_platform


def extract_lagrange(file: BytesIO):
    try:
        with tarfile.open(fileobj=file) as zip_file:
            for member in zip_file.getmembers():
                if member.isfile():
                    with zip_file.extractfile(member) as file:
                        file_name = file.name.split('/')[-1]
                        with open(globals.data_path / file_name, 'wb') as target_file:
                            target_file.write(file.read())
                            return True
    except Exception as error:
        logger.error(F'Lagrange.Onebot 解压失败！错误信息 {error}')
    return False


async def update():
    logger.info('Lagrange.Onebot 正在更新……')
    if globals.lagrange_path is not None:
        globals.lagrange_path.unlink()
    if globals.appsettings_path is not None:
        globals.appsettings_path.unlink()
    return await install()


async def install():
    if globals.lagrange_path is not None:
        logger.warning('检测到 Lagrange.Onebot 已安装，无需再次安装！')
        return True
    system, architecture = parse_platform()
    logger.info(F'检测到当前的系统架构为 {system} {architecture} 正在下载对应的安装包……')
    if response := await download(
            'https://github.com/LagrangeDev/Lagrange.Core/releases/download/'
            F'nightly/Lagrange.OneBot_{system}-{architecture}_net8.0_SelfContained.tar.gz'
    ):
        logger.success(F'Lagrange.Onebot 下载成功！正在安装……')
        if extract_lagrange(response):
            generate_default_settings()
            globals.update_file_paths()
            logger.success('Lagrange.Onebot 安装成功！')
            return True
    logger.error('Lagrange.Onebot 安装失败！')
    return False


async def download(url: str):
    download_bytes = BytesIO()
    async with AsyncClient() as client:
        try:
            async with client.stream('GET', 'https://mirror.ghproxy.com/' + url) as stream:
                if stream.status_code != 200:
                    return False
                async for chunk in stream.aiter_bytes():
                    download_bytes.write(chunk)
                download_bytes.seek(0)
                return download_bytes
        except Exception as error:
            logger.error(F'下载失败！错误信息 {error}')
            return False
