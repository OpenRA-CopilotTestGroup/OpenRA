# OpenRA-Copilot
OpenRA-Copilot 是一个基于 OpenRA 游戏引擎的智能助手工具。
OpenRA使用 asr-llm-python_api-OpenRA的方式，使用大语言模型，协助玩家游玩OpenRA

项目主要由两部分构成，OpenRA和AI副官

## 主要功能

* 根据玩家语音输入操控游戏
* 协助获取游戏信息
* 实时语音识别和指令执行
* AI辅助决策和游戏建议
* 多语言支持（中文/英文）

## 安装教程

1. 编译并运行OpenRA，推荐使用VS(Windows)，VS Code (MacOs/Linux)
2. Copilot\openra_ai 文件夹为AI副官文件夹，执行以下命令安装依赖：
   ```bash
   pip install -r requirement.txt
   ```

## 启动教程

### 方式一：使用启动器（仅Windows）
Copilot\Starter 文件夹中提供了图形界面启动器

### 方式二：命令行启动
设置环境变量并启动：  
假设用GPT-4o，并使用Response模式，简单Sample
```bash
export OPENAI_API_KEY="sk-xxxxxx"
export DEEPSEEK_API_KEY="sk-xxxx"
python3 -m uni_mic.cli --remote-asr --remote-type whisper --debug-mode --gptmodel gpt-4o --single-sample --openai-response-mode
```

## 参数说明

### ASR（语音识别）相关参数
- `--model`: 语音识别模型，默认值："base"
- `--device`: 运行设备，默认值："cpu"
- `--language`: 识别语言，默认值："zh"
- `--remote-asr`: 是否使用远程ASR服务，默认：False
- `--remote-type`: 远程ASR类型，可选："funasr"/"whisper"，默认："funasr"
- `--remote-asr-url`: 远程ASR服务地址
- `--hallucinate-threshold`: 幻听阈值，默认：400
- `--phrase-time-limit`: 短语时间限制（秒），默认：10

### 输入相关参数
- `--input-mode`: 输入模式，默认："mic"
- `--energy`: 音频能量阈值，默认：300
- `--dynamic-energy`: 是否使用动态能量，默认：False
- `--pause`: 停顿检测时间（秒），默认：1.2
- `--save-file`: 是否保存音频文件，默认：False

### 启动器相关参数
- `--gui`: 是否使用图形界面，默认：True
- `--logging-level`: 日志级别，默认："info"
- `--verbose`: 是否显示详细日志，默认：False
- `--gptmodel`: **使用的LLM模型**，默认："gpt-4o"
- `--single-sample`: 单Sample模式，默认：False
- `--debug-mode`: 调试模式，默认：False
- `--openai-response-mode`: OpenAI响应模式，默认：False
- `--openai-realtime-mode`: OpenAI过滤模式，默认：False
- `--use-simplest-prompt`: 使用最简单的提示，默认：False

## 许可证

本项目采用与 OpenRA 相同的 [GPLv3 许可证](LICENSE)。


# OpenRA

A Libre/Free Real Time Strategy game engine supporting early Westwood classics.

* Website: [https://www.openra.net](https://www.openra.net)
* Chat: [#openra on Libera](ircs://irc.libera.chat:6697/openra) ([web](https://web.libera.chat/#openra)) or [Discord](https://discord.openra.net) ![Discord Badge](https://discordapp.com/api/guilds/153649279762694144/widget.png)
* Repository: [https://github.com/OpenRA/OpenRA](https://github.com/OpenRA/OpenRA) ![Continuous Integration](https://github.com/OpenRA/OpenRA/workflows/Continuous%20Integration/badge.svg)

Please read the [FAQ](https://github.com/OpenRA/OpenRA/wiki/FAQ) in our [Wiki](https://github.com/OpenRA/OpenRA/wiki) and report problems at [https://github.com/OpenRA/OpenRA/issues](https://github.com/OpenRA/OpenRA/issues).

Join the [Forum](https://forum.openra.net/) for discussion.

## Play

Distributed mods include a reimagining of

* Command & Conquer: Red Alert
* Command & Conquer: Tiberian Dawn
* Dune 2000

EA has not endorsed and does not support this product.

Check our [Playing the Game](https://github.com/OpenRA/OpenRA/wiki/Playing-the-game) Guide to win multiplayer matches.

## Contribute

* Please read [INSTALL.md](https://github.com/OpenRA/OpenRA/blob/bleed/INSTALL.md) and [Compiling](https://github.com/OpenRA/OpenRA/wiki/Compiling) on how to set up an OpenRA development environment.
* See [Hacking](https://github.com/OpenRA/OpenRA/wiki/Hacking) for a (now very outdated) overview of the engine.
* Read and follow our [Code of Conduct](https://github.com/OpenRA/OpenRA/blob/bleed/CODE_OF_CONDUCT.md).
* To get your patches merged, please adhere to the [Contributing](https://github.com/OpenRA/OpenRA/blob/bleed/CONTRIBUTING.md) guidelines.

## Mapping

* We offer a [Mapping](https://github.com/OpenRA/OpenRA/wiki/Mapping) Tutorial as you can change gameplay drastically with custom rules.
* For scripted mission have a look at the [Lua API](https://docs.openra.net/en/latest/release/lua/).
* If you want to share your maps with the community, upload them at the [OpenRA Resource Center](https://resource.openra.net).

## Modding

* Download a copy of the [OpenRA Mod SDK](https://github.com/OpenRA/OpenRAModSDK) to start your own mod.
* Check the [Modding Guide](https://github.com/OpenRA/OpenRA/wiki/Modding-Guide) to create your own classic RTS.
* There exists an auto-generated [Trait documentation](https://docs.openra.net/en/latest/release/traits/) to get started with yaml files.
* Some hints on how to create new OpenRA compatible [Pixelart](https://github.com/OpenRA/OpenRA/wiki/Pixelart).
* Upload total conversions at [our Mod DB profile](https://www.moddb.com/games/openra/mods).

## Support

* Sponsor a [mirror server](https://github.com/OpenRA/OpenRAWebsiteV3/tree/master/packages) if you have some bandwidth to spare.
* You can immediately set up a [Dedicated](https://github.com/OpenRA/OpenRA/wiki/Dedicated-Server) Game Server.

## License
Copyright (c) OpenRA Developers and Contributors
This file is part of OpenRA, which is free software. It is made
available to you under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version. For more
information, see [COPYING](https://github.com/OpenRA/OpenRA/blob/bleed/COPYING).
