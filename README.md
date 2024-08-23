<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-lagrange

_✨ 一款方便管理 Lagrange.OneBot 的插件。 ✨_

</div>

## 📖 介绍

本插件旨在使用户能够简单的使用 Lagrange.OneBot 来部署机器人。目前实现的功能有：

- 自动配置使其连接上 NoneBot
- 通过 WebUi 控制 Lagrange.
- 提醒用户遇到登录失败的解决方法。
- 根据系统自动安装合适的 Lagrange.OneBot.

<details>
<summary>WebUi</summary>

![1](https://raw.githubusercontent.com/Lonely-Sails/nonebot-plugin-lagrange/master/pictures/1.png)
![2](https://raw.githubusercontent.com/Lonely-Sails/nonebot-plugin-lagrange/master/pictures/2.png)
![3](https://raw.githubusercontent.com/Lonely-Sails/nonebot-plugin-lagrange/master/pictures/3.png)

</details>

## 💿 安装

你可以使用 `pip3 install nonebot-plugin-lagrange` 来安装此插件。

## ⚙️ 配置

在 NoneBot2 项目的`.env`文件中添加下表中的必填配置

|          配置项           | 必填 |   默认值    |            说明             |
|:----------------------:|:--:|:--------:|:-------------------------:|
|     lagrange_path      | 否  | Lagrange | Lagrange.OneBot 的安装和运行目录。 |
|  lagrange_auto_start   | 否  |   True   |  是否在检测到有安装 Lgr 的情况下自动启动。  |
| lagrange_auto_install  | 否  |   True   |    是否在未安装 Lgr 的情况自动安装     |
| lagrange_max_cache_log | 否  |   500    |         最大缓存多少行日志         |
|     lagrange_webui     | 否  |   True   |        是否启用 WebUi         |
|  lagrange_webui_token  | 否  |    空     |     登录 WebUi 的 token      |

## 🎉 使用

### WebUi

在启动机器人时，你应该会看到一行日志：

```log
08-19 10:50:54 [INFO] nonebot_plugin_lagrange | WebUi http://127.0.0.1:8080/lagrange?token=ijr...
```

其中 `WebUi` 字段后面的链接就是 WebUi 的地址。请注意，后面的 token 参数即为登录密码，请注意保管。你可以自己设置配置项 `Lagrange_webui_token` ，若检测到为空时将会自动生成一个 token 并储存在拉格兰目录下的 `token.bin` 文件中。

将这个链接复制到浏览器内并打开，如若出现界面则登录成功。

### 指令表

|   名称   |  权限  | 说明      |
|:------:|:----:|:--------|
| status | 超级用户 | 查看拉格兰状态 |

## 计划功能

- [ ] 监控拉格兰日志，分析机器人的消息。

## 🙏 鸣谢

> [Lagrange](https://lagrangedev.github.io/Lagrange.Doc/)
