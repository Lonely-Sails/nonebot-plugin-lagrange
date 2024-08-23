import time
import platform
from random import choice
from string import ascii_letters, digits
from subprocess import Popen, PIPE

from . import globals


def generate_token():
    words = (ascii_letters + digits)
    return ''.join([choice(words) for _ in range(100)])


def generate_default_settings():
    path = next(globals.data_path.rglob('Lagrange.OneBot*'))
    path.chmod(0x755)
    task = Popen(str(path.absolute()), stdout=PIPE, cwd=str(globals.data_path))
    while not tuple(globals.data_path.rglob('appsettings.json')):
        time.sleep(2)
    task.terminate()


def parse_platform():
    system = platform.system()
    architecture = platform.machine()
    system_mapping = {'Linux': 'linux', 'Darwin': 'osx', 'Windows': 'win'}
    if system == 'Windows':
        architecture = 'x64' if architecture == 'AMD64' else 'x86'
    elif system == 'Darwin':
        architecture = 'x64' if architecture == 'x86_64' else 'arm64'
    elif system == 'Linux':
        architecture = 'x64' if architecture == 'x86_64' else 'arm'
    return system_mapping[system], architecture


def parse_log_level(log: str):
    for level in ('info', 'warn'):
        if log.startswith(level):
            return False
    if log.startswith('['):
        _, log_class, log_level, *message = log.split()
        return log_class, log_level, ' '.join(message)
