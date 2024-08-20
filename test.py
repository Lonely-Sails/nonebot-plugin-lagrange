import nonebot

from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

nonebot.init()
nonebot.load_plugin('nonebot_plugin_lagrange')

driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

if __name__ == '__main__':
    nonebot.run()
