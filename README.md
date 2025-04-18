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

# Demo使用基础指南
  
1.本Demo仅支持OpenRA-RedAlter模式，请选择该模式启动  
2.本Demo仅支持玩家使用苏联系列阵营  
3.暂时不支持友方，请全部敌对  
4.支持局域网联机 ，可双方都使用OpenRA-Copilot对战
5.暂不支持超级武器的使用（建筑可以建造）

## 兵种 & 建筑基本名称

支持所有名称和别名，列表以外的暂未支持

### 建筑单位
| 建筑名称 | 别名 |
|---------|------|
| 发电厂 | 电厂、小电、小电厂、基础电厂 |
| 兵营 | 兵工厂、步兵营、训练营 |
| 矿场 | 采矿场、矿、精炼厂、矿石精炼厂 |
| 战车工厂 | 车间、坦克厂、坦克工厂、载具工厂 |
| 雷达站 | 雷达、侦察站、雷达圆顶 |
| 维修厂 | 修理厂、维修站、修理站 |
| 储存罐 | 井、存钱罐、储油罐、资源储存罐 |
| 核电站 | 核电厂、大电、大电厂、高级电厂 |
| 空军基地 | 机场、飞机场、航空站 |
| 科技中心 | 高科技、高科技中心、研究中心、实验室 |
| 军犬窝 | 狗窝、狗屋、狗舍、狗棚、军犬训练所 |
| 火焰塔 | 喷火塔、喷火碉堡、防御塔 |
| 特斯拉塔 | 电塔、特斯拉线圈、高级防御塔 |
| 防空导弹 | 防空塔、防空、山姆飞弹 |
| 铁幕装置 | 铁幕、铁幕防御系统 |
| 核弹发射井 | 核弹、导弹发射井、核导弹井 |

### 步兵单位
| 单位名称 | 别名 |
|---------|------|
| 步兵 | 枪兵、步枪兵、普通步兵 |
| 火箭兵 | 火箭筒兵、炮兵、火箭筒、导弹兵 |
| 工程师 | 维修工程师、技师 |
| 掷弹兵 | 手雷兵、手雷、榴弹兵 |
| 军犬 | 狗、小狗、攻击犬 |
| 喷火兵 | 火焰兵、火焰喷射兵 |
| 间谍 | 特工、潜伏者 |
| 磁暴步兵 | 电击兵、电兵、突击兵 |

### 载具单位
| 单位名称 | 别名 |
|---------|------|
| 采矿车 | 矿车、矿物收集车 |
| 装甲运输车 | 装甲车、运兵车 |
| 防空炮车 | 防空车、移动防空车 |
| 基地车 | 建造车、移动建设车 |
| 轻坦克 | 轻坦、轻型坦克、轻型装甲车 |
| 重型坦克 | 重坦、犀牛坦克、犀牛 |
| V2火箭发射车 | 火箭炮、V2火箭 |
| 地雷部署车 | 雷车、布雷车 |
| 超重型坦克 | 猛犸坦克、猛犸、天启坦克、天启 |
| 特斯拉坦克 | 磁暴坦克、磁能坦克、电击坦克 |
| 震荡坦克 | 地震坦克、震波坦克 |

### 空中单位
| 单位名称 | 别名 |
|---------|------|
| 运输直升机 | 运输机、空运 |
| 雌鹿直升机 | 雌鹿攻击直升机、雌鹿、武装直升机 |
| 黑鹰直升机 | 黑鹰、武装直升机 |
| 雅克战机 | 雅克、雅克攻击机、苏联战机 |
| 长弓武装直升机 | 长弓、长弓直升机 |
| 米格战机 | 米格、米格战斗机 |

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
