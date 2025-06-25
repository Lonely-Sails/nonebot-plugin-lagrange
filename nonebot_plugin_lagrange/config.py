from pathlib import Path
from pydantic import BaseModel
from ipaddress import IPv4Address
from typing import Optional


class Config(BaseModel):
    port: int = 8080
    host: IPv4Address = IPv4Address('127.0.0.1')

    onebot_access_token: str = ''

    lagrange_path: Path = Path('Lagrange')

    lagrange_auto_start: bool = True
    lagrange_auto_install: bool = True

    lagrange_max_cache_log: int = 500

    lagrange_webui: bool = True
    lagrange_webui_token: Optional[str] = None
    lagrange_github_proxy: str = 'https://cdn.gh-proxy.com/'
    lagrange_sign_server_url: str = 'https://sign.lagrangecore.org/api/sign/30366'
