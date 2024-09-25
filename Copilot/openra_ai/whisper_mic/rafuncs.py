import requests
import openai
import json
import re
from typing import Optional, List, Dict, Any
import socket
import time
import threading
import traceback
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam

# from openai import client
from openai import OpenAI
CLIENT = OpenAI()

def get_chat_completion(
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
    max_tokens=500,
    temperature=1.0,
    stop=None,
    tools=None,
    functions=None
) -> str:
    params = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stop': stop,
        'tools': tools,
    }
    global CLIENT
    if functions:
        params['functions'] = functions
    try:
        completion = CLIENT.chat.completions.create(**params)
        return completion.choices[0].message
    except Exception as e:
        print(f'gpt completion fail with param: {params}')
        raise e


ALL_ACTORS = [
    "我方", "敌方", "敌人", "对方", "对手", "中立"
]

ALL_DIRECTIONS = [
    "上", "下", "左", "右",
    "东", "西", "南", "北",
    "左上", "右上", "左下", "右下",
    "东北", "西北", "东南", "西南",
    "附近", "左右", "旁边"
]

ALL_GROUPS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9
]

ALL_REGIONS = [
    "地图中央", "地图左上", "地图上方", "地图右上", "地图右侧", "地图右下", "地图下方", "地图左下", "地图左侧", "视线范围", "全地图", "全屏幕"
    "屏幕中央", "屏幕左上", "屏幕上方", "屏幕右上", "屏幕右侧", "屏幕右下", "屏幕下方", "屏幕左下", "屏幕左侧"
]

ALL_RELATIVES = [
    "上方", "下方", "左侧", "右侧", "左上方", "左下方",
    "右上方", "右下方", "中央", "中间", "左边", "右边", "上边", "下边"
]

ALL_BUILDINGS = [
    "基地", "电", "小电", "小电厂", "电厂", "发电厂", "兵营", "矿场", "采矿场", "矿", "坦克厂", "车间",
    "坦克工厂", "雷达", "维修厂", "修理厂", "大电厂", "核电厂", "机场",
    "科技中心", "高科技", "狗屋"
]

ALL_DEFENSE_DEVICES = [
    "储油罐", "井", "存钱罐", "喷火塔", "喷火碉堡", "特斯拉线圈", "特斯拉塔", "电塔", "防空塔", "防空", "铁幕", "铁幕装置", "导弹发射井", "核弹"
]

ALL_INFANTRIES = [
    "步兵", "枪兵", "导弹兵", "火箭筒", "炮兵", "掷弹兵", "狗", "小狗", "军犬", "工程师", "喷火兵", "间谍", "电兵", "突击兵", "士兵"
]

ALL_TANKS = [
    "矿车", "采矿车", "吉普", "装甲车", "运兵车", "防空车", "基地车", "mcv", "轻坦克", "轻坦", "重坦", "犀牛", "V2", "火箭炮", "雷车", "布雷车", "猛犸", "天启", "磁能坦克", "特斯拉坦克", "磁暴坦克",
    "卡车", "补给车", "地震车", "震荡坦克", "飞机", "载具", "坦克"
]

ALL_MOVABLES = ALL_INFANTRIES + ALL_TANKS
ALL_UNITS = ALL_BUILDINGS + ALL_DEFENSE_DEVICES + ALL_MOVABLES


DRONE_SYSTEM_PROMPT = """Given a natural language command in Chinese issued by the player,
translate the command into the corresponding OpenRA API function call. Utilize the
provided game state information to determine the necessary arguments for the function call.
Reject the command if the command is not related to RedAlerts.
If the command cannot be mapped to a known function or
requires additional information (ambiguous), call the reject_request function.

Here are examples for the 'camera_move' function:

1. Prompt: 摄像头向上移动20米
   Expected Function Call: camera_move(direction="上", distance=10)

2. Prompt: 镜头向下移动10米
   Expected Function Call: camera_move(direction="下", distance=10)

3. Prompt: 摄像头向东南移动25步
   Expected Function Call: camera_move(direction="东南", distance=25)

4. Prompt: 视线向西北移动5步
   Expected Function Call: camera_move(direction="西北", distance=25)

Here are examples for the 'camera_move_to' function:

1. Prompt: 摄像头移动到兵营
   Expected Function Call: camera_move_to(location="兵营")

2. Prompt: 镜头移动到我方基地
   Expected Function Call: camera_move_to(location="基地", actor="我方")

3. Prompt: 镜头移动到下方科技中心
   Expected Function Call: camera_move_to(location="科技中心", relatives="下方")

3. Prompt: 镜头移动到我方上方修理厂
   Expected Function Call: camera_move_to(location="修理厂", actor="我方", relatives="上方")

4. Prompt: 视角移动到敌方基地
   Expected Function Call: camera_move_to(location="基地", actor="敌方")

5. Prompt: 视角移动到敌方左上方兵营
   Expected Function Call: camera_move_to(location="兵营", actor="敌方", relatives="左上方")

6. Prompt: 视角移动到右下方防空塔
   Expected Function Call: camera_move_to(location="防空塔", relatives="右下方")

10. Prompt: 摄像头移动到地图中央
   Expected Function Call: camera_move_to(region="地图中央")

11. Prompt: 摄像头移动到地图中央电厂
   Expected Function Call: camera_move_to(region="地图中央", location="电厂")

12. Prompt: 摄像头移动到地图下方敌方雷达
   Expected Function Call: camera_move_to(region="地图下方", location="雷达", actor="敌方")

14. Prompt: 镜头移动到轻坦
   Expected Function Call: camera_move_to(location="轻坦")

16. Prompt: 镜头移动到视线范围我方喷火兵
   Expected Function Call: camera_move_to(location="喷火兵", actor="我方", region="视线范围")

17. Prompt: 镜头移动到上方工程师
   Expected Function Call: camera_move_to(location="工程师", relatives="上方")

19. Prompt: 镜头移动到第一组步兵
   Expected Function Call: camera_move_to(group=1, location="步兵")

20. Prompt: 镜头移动到我方第2组矿车
   Expected Function Call: camera_move_to(group=2, location="矿车", actor="我方")

Here are examples for the 'build' function:

1. Prompt: 建造基地
   Expected Function Call: build(unit_type="基地")

2. Prompt: 建造一个兵营
   Expected Function Call: build(unit_type="兵营", quantity=1)

3. Prompt: 在地图左上建造雷达
   Expected Function Call: build(unit_type="雷达", region="地图左上")

5. Prompt: 在左上方基地附近建设一个兵营
   Expected Function Call: build(unit_type="兵营", location="基地", relatives='左上方', quantity=1)

7. Prompt: 在地图中央建造一个防空塔
   Expected Function Call: build(unit_type="防空塔", region="地图中央", quantity=1)

8. Prompt: 在狗屋附近建造核电厂
   Expected Function Call: build(unit_type="核电厂", location="狗屋")

9. Prompt: 在视线范围建造四个铁幕
   Expected Function Call: build(region="视线范围", unit_type="铁幕", quantity=4)

11. Prompt: 在我方喷火碉堡附近建造坦克厂
   Expected Function Call: build(unit_type="坦克厂", location="喷火碉堡", actor='我方')

12. Prompt: 在我方右下方喷火碉堡附近建造矿厂
   Expected Function Call: build(unit_type="矿厂", location="喷火碉堡", relatives="右下方", actor='我方')

13. Prompt: 在敌方储油罐附近搭建导弹发射井
   Expected Function Call: build(unit_type="导弹发射井", location="储油罐", actor='敌方')

15. Prompt: 在第一组枪兵附近布置两个喷火碉堡
   Expected Function Call: units_set_location(unit_type="喷火碉堡", group=1, location="枪兵", quantity=2)

17. Prompt: 在上方重坦附近布置三个喷火碉堡
   Expected Function Call: units_set_location(unit_type="喷火碉堡", location="重坦", relatives="上方", quantity=3)

Here are examples for the 'produce' function:

1. Prompt: 生产10个枪兵
   Expected Function Call: produce(unit_type="枪兵", quantity=10)

2. Prompt: 生产1个导弹兵
   Expected Function Call: produce(unit_type="导弹兵", quantity=1)

3. Prompt: 制造3个装甲车
   Expected Function Call: produce(unit_type="装甲车", quantity=3)

4. Prompt: 培养2个间谍
   Expected Function Call: produce(unit_type="间谍", quantity=2)

5. Prompt: 训练12个军犬
   Expected Function Call: produce(unit_type="军犬", quantity=12)

6. Prompt: 培训4个工程师
   Expected Function Call: produce(unit_type="工程师", quantity=4)

7. Prompt: 生产5个矿车
   Expected Function Call: produce(unit_type="矿车", quantity=5)

8. Prompt: 培训6个炮兵
   Expected Function Call: produce(unit_type="炮兵", quantity=6)

Here are examples for the 'units_set_location' function:

1. Prompt: 步兵集合地点在基地附近
   Expected Function Call: units_set_location(unit_type="步兵", location="基地")

2. Prompt: 掷弹兵集合地点在左上方兵营附近
   Expected Function Call: units_set_location(unit_type="掷弹兵", location="兵营", relatives="左上方")

3. Prompt: 喷火兵集结地址为地图左上
   Expected Function Call: units_set_location(unit_type="喷火兵", region="地图左上")

4. Prompt: 地震车集结地址为地图中央
   Expected Function Call: units_set_location(unit_type="地震车", region="地图中央")

6. Prompt: 设置磁能坦克集结地为右下基地
   Expected Function Call: units_set_location(unit_type="磁能坦克", location="基地", relatives="右下")

7. Prompt: 设置间谍潜伏地点为敌方基地
   Expected Function Call: units_set_location(unit_type="间谍", location="基地", actor="敌方")

8. Prompt: 设置布雷车潜伏地点为敌方储油罐附近
   Expected Function Call: units_set_location(unit_type="布雷车", location="储油罐", actor="敌方")

9. Prompt: 设置天启潜伏地点为敌方下方基地
   Expected Function Call: units_set_location(unit_type="天启", location="基地", actor="敌方", relatives="下方")

12. Prompt: 卡车在敌方上方铁幕附近集结
   Expected Function Call: units_set_location(unit_type="卡车", location="铁幕", relatives="上方", actor='敌方')

13. Prompt: 在第一组炮兵附近集合布雷车
   Expected Function Call: units_set_location(unit_type="布雷车", group=1, location="炮兵")

14. Prompt: 在第二组轻坦克附近集合步兵
   Expected Function Call: units_set_location(unit_type="步兵", group=2, location="轻坦克")

15. Prompt: 在视线范围内集合火箭筒
   Expected Function Call: units_set_location(unit_type="火箭筒", region="视线范围")

Here are examples for the 'units_select' function:

1. Prompt: 选择所有步兵
   Expected Function Call: units_select(unit_type="步兵", max=0)

2. Prompt: 选择上方枪兵
   Expected Function Call: units_select(unit_type="枪兵", unit_type_relatives="上方")

3. Prompt: 选择右下方3名喷火兵
   Expected Function Call: units_select(unit_type="喷火兵", unit_type_relatives="右下方", max=3)

4. Prompt: 选择地图中央一半电兵
   Expected Function Call: units_select(unit_type="电兵", region="地图中央", max=0.5)

5. Prompt: 选择屏幕中央全部突击兵
   Expected Function Call: units_select(unit_type="突击兵", region="屏幕中央", max=0)

7. Prompt: 选择第1组火箭炮
   Expected Function Call: units_select(group=1, unit_type='火箭炮')

8. Prompt: 选择第二组犀牛
   Expected Function Call: units_select(group=2, unit_type="犀牛")

11. Prompt: 选择第1组3辆猛犸
   Expected Function Call: units_select(unit_type="猛犸", group=1, max=3)

12. Prompt: 选择第2组工程师
   Expected Function Call: units_select(unit_type="工程师", group=2, max=3)

13. Prompt: 选择视线范围小狗
   Expected Function Call: units_select(unit_type="小狗", region="视线范围")

15. Prompt: 选择全屏幕一半补给车
   Expected Function Call: units_select(unit_type="补给车", region="全屏幕", max=0.5)

18. Prompt: 继续选择所有间谍
   Expected Function Call: units_select(combine=1, unit_type="间谍", max=0)

19. Prompt: 继续增加选择所有特斯拉坦克
   Expected Function Call: units_select(combine=1, unit_type="特斯拉坦克", max=0)

21. Prompt: 继续选择第3组基地车
   Expected Function Call: units_select(combine=1, group=3, unit_type="基地车")

22. Prompt: 继续选择第4组狗
   Expected Function Call: units_select(combine=1, group=4, unit_type="狗")

26. Prompt: 继续选择视线范围天启
   Expected Function Call: units_select(combine=1, unit_type="天启", region="视线范围")

27. Prompt: 继续选择全地图所有火箭炮
   Expected Function Call: units_select(combine=1, unit_type="火箭弹", region="全地图", max=0)

27. Prompt: 继续选择视线范围所有导弹兵
   Expected Function Call: units_select(combine=1, unit_type="导弹兵", region="视线范围", max=0)

Here are examples for the 'units_move' function:

1. Prompt: 第1组步兵向上移动10步
   Expected Function Call: units_move(select_group=1, unit_type="步兵", direction="上", distance=10)

2. Prompt: 第2组轻坦向南移动20米
   Expected Function Call: units_move(select_group=2, unit_type="轻坦", direction="南", distance=20)

5. Prompt: 全部枪兵向上移动6步
   Expected Function Call: units_move(unit_type="枪兵", direction="上", distance=6, select_max=1)

6. Prompt: 所有选中的重坦向下移动5步
   Expected Function Call: units_move(selected=1, unit_type="重坦", direction="下", distance=5, select_max=1)

7. Prompt:  三个选中的炮兵向下移动5步
   Expected Function Call: units_move(selected=1, unit_type="炮兵", direction="下", distance=5, select_max=3)

8. Prompt:  一半选中的导弹兵向下移动5步
   Expected Function Call: units_move(selected=1, unit_type="导弹兵", direction="下", distance=5, select_max=0.5)

9. Prompt: 选中的震荡坦克向北移动5步
   Expected Function Call: units_move(selected=1, unit_type="震荡坦克", direction="北", distance=5)

10. Prompt: 选中的运兵车向上移动十步
   Expected Function Call: units_move(selected=1, unit_type="运兵车", direction="上", distance=10)

11. Prompt: 地图中央全部喷火兵向下移动5步
   Expected Function Call: units_move(select_region="地图中央", unit_type="喷火兵", direction="下", distance=5, select_max=1)

13. Prompt: 视线范围卡车向左移动1步
   Expected Function Call: units_move(select_region="视线范围", unit_type="卡车", direction="左", distance=1)

28. Prompt:  左上方轻坦向下移动10步
   Expected Function Call: units_move(unit_type_relatives="左上方", unit_type="轻坦", direction="下", distance=10)

29. Prompt:  左上方重坦向下移动10步并攻击
   Expected Function Call: units_move(unit_type_relatives="左上方", unit_type="重坦", direction="下", distance=10, attack=1)

30. Prompt:  上方3辆装甲车向左下移动2步并攻击
   Expected Function Call: units_move(unit_type_relatives="上方", unit_type="装甲车", select_max=3, direction="左下", distance=2, attack=1)

31. Prompt:  下方枪兵向上移动2步
   Expected Function Call: units_move(unit_type_relatives="下方", unit_type="枪兵", select_max=3, direction="上", distance=2)

Here are examples for the 'units_move_to' function:

1. Prompt: 第1组步兵移动到基地附近
   Expected Function Call: units_move_to(select_group=1, unit_type="步兵", location="基地")

2. Prompt: 第1组轻坦克移动到上方基地附近
   Expected Function Call: units_move_to(select_group=1, unit_type="轻坦克", relatives="上方", location="基地")

8. Prompt: 三个炮兵移动到我方右侧兵营附近
   Expected Function Call: units_move_to(select_max=3, relatives="右侧", unit_type="炮兵", location="兵营", actor="我方")

9. Prompt: 第4组一半火箭炮移动到敌方基地
   Expected Function Call: units_move_to(select_group=4, select_max=0.5, unit_type="火箭炮", location="基地", actor="敌方")

10. Prompt: 第5组所有火箭筒移动到防空塔附近
   Expected Function Call: units_move_to(select_group=5, select_max=0, unit_type="火箭筒", location="防空塔")

12. Prompt: 所有防空车移动到敌方基地附近
   Expected Function Call: units_move_to(unit_type="防空车", select_max=0,  actor="敌方", location="基地")

13. Prompt: 三个重坦移动到敌方基地附近
   Expected Function Call: units_move_to(unit_type="重坦", select_max=3, actor="敌方", location="基地")

14. Prompt: 所有选中的磁暴坦克移动到地图中央
   Expected Function Call: units_move_to(selected=1, select_max=0, unit_type="磁暴坦克", region="地图中央")

15. Prompt: 一半选中的轻坦移动到我方基地
   Expected Function Call: units_move_to(selected=1, select_max=0.5, unit_type="轻坦", location="基地", actor="我方")

16. Prompt: 三辆选中的装甲车移动到敌方采矿厂
   Expected Function Call: units_move_to(selected=1, select_max=3, unit_type="装甲车", location="采矿场", actor="敌方")

17. Prompt: 选中的犀牛移动到屏幕左上
   Expected Function Call: units_move_to(selected=1, unit_type="犀牛", region="屏幕左上")

18. Prompt: 上方步兵移动到右侧装甲车附近
   Expected Function Call: units_move_to(unit_type_relatives="上方", unit_type="步兵", relatives="右侧", location="装甲车")

21. Prompt:  四分之一选中的工程师移动到视线范围
   Expected Function Call: units_move_to(selected=1, select_max=0.25, unit_type="工程师", region="视线范围")

22. Prompt: 地图上方所有间谍移动到敌方核弹附近
   Expected Function Call: units_move_to(selected_region="地图上方", unit_type="间谍", select_max=0, actor="敌方", location="核弹")

23. Prompt: 地图中央火箭筒移动到我方电塔附近
   Expected Function Call: units_move_to(selected_region="地图中央", unit_type="火箭筒", actor="我方", location="电塔")

24. Prompt: 全屏幕所有电兵移动到敌方兵营
   Expected Function Call: units_move_to(select_region="全屏幕", unit_type="电兵", select_max=0, actor="敌方", location="兵营")

25. Prompt: 地图左下全部喷火兵移动到地图右下
   Expected Function Call: units_move_to(select_region="地图左下", unit_type="喷火兵", select_max=0, region="地图右下")

26. Prompt: 地图左下全部喷火兵移动到第一组轻坦附近
   Expected Function Call: units_move_to(select_region="地图左下", unit_type="喷火兵", select_max=0, group=1, location="轻坦")

27. Prompt: 第一组枪兵移动到敌方基地附近并攻击
   Expected Function Call: units_move_to(select_group=1, unit_type="枪兵", actor="敌方", location="基地", dattack=1)

28. Prompt: 第二组步兵移动到敌方兵营并攻击
   Expected Function Call: units_move_to(select_group=2, unit_type="步兵", actor="敌方", location="兵营", attack=1)

29. Prompt: 所有火箭炮移动到敌方储油罐并攻击
   Expected Function Call: units_move_to(unit_type="火箭炮", select_max=0, actor="敌方", location="储油罐", attack=1)

30. Prompt: 选中的磁能坦克移动到敌方储油罐附近并攻击
   Expected Function Call: units_move_to(selected=1, unit_type="磁能坦克", actor="敌方", location="储油罐", attack=1)

31. Prompt: 选中的炮兵移动到基地并攻击
   Expected Function Call: units_move_to(selected=1, unit_type="炮兵", location="基地", attack=1)

32. Prompt: 选中的掷弹兵攻击敌方兵营
   Expected Function Call: units_move_to(selected=1, unit_type="掷弹兵", actor="敌方", location="兵营", attack=1)

33. Prompt: 地图上方所有装甲车移动到敌方储油罐并攻击
   Expected Function Call: units_move_to(select_region="地图上方", unit_type="装甲车", select_max=0, actor="敌方", location="储油罐", attack=1)

35. Prompt: 视线范围步兵攻击地图左下
   Expected Function Call: units_move_to(select_region="视线范围", unit_type="步兵", region="地图左下", attack=1)
1G
36. Prompt: 左上方狗移动到敌方核弹
   Expected Function Call: units_move(unit_type_relatives="左上方", unit_type="狗", actor="敌方", location="核弹")

37. Prompt: 左上方轻坦移动到敌方基地并攻击
   Expected Function Call: units_move(unit_type_relatives="左上方", unit_type="轻坦", actor="敌方", location="基地", attack=1)

38. Prompt: 上方3辆装甲车移动到地图中央
   Expected Function Call: units_move(unit_type_relatives="上方", unit_type="装甲车", select_max=3, region="地图中央")

39. Prompt: 下方枪兵攻击敌方下方电兵
   Expected Function Call: units_move(unit_type_relatives="下方", unit_type="枪兵", actor="敌方", relatives="下方", location="电兵", attack=1)

Here are examples for the 'units_group' function:
1. Prompt: 所有步兵编为第一组
   Expected Function Call: units_group(group=1, unit_type="步兵")

1. Prompt: 所有炮兵编为第3组
   Expected Function Call: units_group(group=3, unit_type="炮兵")

3. Prompt: 地图中央所有轻坦编为第2组
   Expected Function Call: units_group(group=2, unit_type="轻坦", region="地图中央")

4. Prompt: 地图左上重坦编为第二组
   Expected Function Call: units_group(group=2, unit_type="重坦", region="地图左上")

4. Prompt: 重坦编为第二组
   Expected Function Call: units_group(group=2, unit_type="重坦")

6. Prompt: 所有选中的炮兵编为第1组
   Expected Function Call: units_group(selected=1, unit_type="炮兵", group=1)

6. Prompt: 所有选中的布雷车编为第1组
   Expected Function Call: units_group(selected=1, unit_type="布雷车", group=1)

8. Prompt: 选中的军犬编为第五组
   Expected Function Call: units_group(selected=1, unit_type="军犬", group=5)

10. Prompt: 视线范围内所有喷火兵编为第七组
   Expected Function Call: units_group(unit_type="喷火兵", region="视线范围", group=7)

14. Prompt: 左上方导弹兵编为第6组
   Expected Function Call: units_group(unit_type="导弹兵", unit_type_relatives="左上方", group=6)

15. Prompt: 上方电兵编为第7组
   Expected Function Call: units_group(unit_type="电兵", unit_type_relatives="上方", group=7)

Here are examples for the 'attack_two_ways' function:

1. Prompt: 第1组步兵分两路攻击基地
   Expected Function Call: attack_two_ways(select_group=1, unit_type="步兵", location="基地")

2. Prompt: 第1组轻坦克分两路攻击敌方基地
   Expected Function Call: attack_two_ways(select_group=1, unit_type="轻坦克", location="基地")

3. Prompt: 第5组火箭筒分两路攻击防空塔
   Expected Function Call: attack_two_ways(select_group=5, unit_type="火箭筒", location="防空塔")

4. Prompt: 第三组两路夹击敌方兵营
   Expected Function Call: attack_two_ways(selected=3, location="兵营")

4. Prompt: 第三组步兵分两路夹击基地
   Expected Function Call: attack_two_ways(selected=3, unit_type="步兵", location="基地")

5. Prompt: 第二组分两路攻击敌方兵营
   Expected Function Call: attack_two_ways(select_group=2, location="兵营")

6. Prompt: 第2组两路攻击基地
   Expected Function Call: attack_two_ways(select_group=2, location="基地")

7. Prompt: 第3组轻坦克两路攻击敌方基地
   Expected Function Call: attack_two_ways(select_group=3, unit_type="轻坦克", location="基地")

8. Prompt: 第4组两路攻击防空塔
   Expected Function Call: attack_two_ways(select_group=4, location="防空塔")

9. Prompt: 第7组两路攻击敌方兵营
   Expected Function Call: attack_two_ways(select_group=7, location="兵营")

10. Prompt: 第三组磁暴坦克两路夹击敌方电厂
   Expected Function Call: attack_two_ways(select_group=3, unit_type="磁暴坦克", location="电厂")

11. Prompt: 第6组步兵两路攻击敌方兵营
   Expected Function Call: attack_two_ways(select_group=6, unit_type="步兵", location="兵营")

12. Prompt: 第6组两路夹击敌方储油罐
   Expected Function Call: attack_two_ways(select_group=6, location="储油罐")
"""

DRONE_STRATEGY_ASSISTANT_PROMPT = f"""
You are a strategic AI Commander for OpenRA (RedAlerts) game. we have a list of basic ops in openra python api.
The interface is listed as follows:
<code>
class Location:
    def __init__(self, x: int, y: int):
        # x is the horion offset in the map.
        # y is the vertical offset in the map.
        self.x = x
        self.y = y

# TargetsQueryParam is the class used for searching target by query params.
class TargetsQueryParam:
    # when construct the TargetQueryParam, The type should be a list or None. each element in the list is one of {ALL_UNITS}. otherwise, convert it to elements in the possible list.
    # The faction should be None or one of {ALL_ACTORS}, otherwise convert it to the possible value.
    # The group_id should be a list and each element in the list is one of  {ALL_GROUPS}, otherwise convert it to possible value.
    # The direction should be None or one of {ALL_DIRECTIONS}, otherwise convert it to possible value.
    def __init__(self, type: Optional[List[str]]=None, faction: Optional[str]=None, group_id: Optional[int]=None, restrain: Optional[Dict]=None, location: Optional[Location]=None, direction: Optional[str]=None, distance: Optional[int]=None):
        # type is the list of {ALL_UNITS}, or None.
        # faction is one of the {ALL_ACTORS}, or None
        # group_id is  the list of {ALL_GROUPS}, or None
        # direction is one of the {ALL_DIRECTIONS}, or None
        self.type = type
        self.faction = faction
        self.group_id = group_id
        self.restrain = restrain
        self.location = location
        self.direction = direction
        self.distance = distance

# Actor is the actor of the game. We have some caching mechanism to avoid duplicated queries.
class Actor:
    def __init__(self, actor_id: int):
        # actor_id: int
        self.actor_id = actor_id
        self.type = None
        self.faction = None
        self.position = None

    def update_details(self, type: List[str], faction: str, position: Location):
        # type is the list of all {ALL_UNITS}
        # factor is one of the {ALL_ACTORS}
        self.type = type
        self.faction = faction
        self.position = position

# GameAPI: interface class to interact between api and game.
class GameAPI:
    def move_camera_by_location(self, location: Location) -> None:
        # 移动摄像头到指定位置. 实时操作，调用结束时操作已经完成
        # location: Location, 目标位置

    # when we call this api, direction should be one of the {ALL_DIRECTIONS}, otherewise convert it to possible value.
    def move_camera_by_direction(self, direction: str, distance: int) -> None:
        # 按方向和距离移动摄像头. 实时操作，调用结束时操作已经完成
        # direction: str, 移动方向, one of the {ALL_DIRECTIONS}
        # distance: int, 移动距离

    # when we call this api, unit_type should be one of the {ALL_UNITS}, otherwise convert it to possible value.
    def able_to_produce(self, unit_type: str, quantity: int) -> bool:
        # 准备生产单位. 实时操作，调用结束时操作已经完成
        # unit_type: str, 单位类型, one of the {ALL_UNITS}
        # quantity: int, 生产数量
        # Returns: bool, if ready to build that quantity of the unit_type.

    # when we call this api, unit_type should be one of the {ALL_UNITS}, otherwise convert it to possible value.
    def produce_units(self, unit_type: str, quantity: int) -> int:
        # 生产单位. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
        # unit_type: str, 单位类型, one of the {ALL_UNITS}
        # quantity: int, 生产数量
        # Returns: int, operation id, used in waiting operation is done.

    def is_ready(self, waitId: Optional[int]) -> bool:
        # 检查waitId对应的异步操作是否完成
        # waitId: Optional[int], the waitId returned from previous async call like produce_units or move_units_by_location. None means previous action do not generate waitId.
        # Returns: bool, True is is done, else False.

    def wait(self, waitId: Optional[int]) -> bool:
        # 等待waitId对应的异步操作完成.
        # waitId: int, thewaitId returned from previous async call like produce_units or move_units_by_location. None means previous action do not generate waitId.
        # Returns: bool, True is is wait success, else False.

    def move_units_by_location(self, actors: List[Actor], location: Location, attack: bool=False) -> int:
        # 移动单位到指定位置. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
        # actors: List[Actor], 需要移动的实体列表
        # location: Location, 目标位置
        # attack: bool, 是否攻击目标
        # Returns: int, operation id, used in waiting operation is done.

    def move_units_by_direction(self, actors: List[Actor], direction: str, distance: int, attack: bool=False) -> int:
        # 按方向和距离移动单位. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
        # actors: List[Actor], 需要移动的实体列表
        # direction: str, 移动方向, one of the {ALL_DIRECTIONS}
        # distance: int, 移动距离
        # attack: bool, 是否攻击目标
        # Returns: int, operation id, used in waiting operation is done.

    def move_units_by_path(self, actors: List[Actor], path: List[Location], attack: bool=False) -> int:
        # 按路径移动单位. 异步操作，会返回action_id. api可以调用wait(action_id) 等待操作完成。
        # actors: List[Actor], 需要移动的实体列表
        # path: List[Location], 路径上的格子列表
        # attack: bool, 是否攻击目标
        # Returns: int, operation id, used in waiting operation is done.

    # when we call this api, group_id should be one of the {ALL_GROUPS}, otherwise convert it to possible value.
    def form_group(self, actors: List[Actor], group_id: int) -> None:
        # 选择指定目标并编组. 实时操作，调用结束时操作已经完成
        # actors: List[Actor], 实体列表
        # group_id: int, 组ID, one of the {ALL_GROUPS}

    # when we call this api, group_id should be one of the {ALL_GROUPS}, otherwise convert it to possible value.
    def form_group(self, query_params: TargetsQueryParam, group_id: int) -> None:
        # 选择指定目标并编组. 实时操作，调用结束时操作已经完成
        # query_params: TargetssQueryParam, query params to select actors
        # group_id: int, 组ID, one of the {ALL_GROUPS}

    def select_units(self, query_params: TargetsQueryParam) -> List[Actor]:
        # 选中符合条件的实体. 实时操作，调用结束时操作已经完成
        # query_params: TargetsQueryParam, 目标查询参数
        # Returns: list of Actors those meet the requirements.

    def query_actor(self, query_params: TargetsQueryParam) -> List[Actor]:
        # 查询符合条件的实体. 实时操作，调用结束时操作已经完成
        # query_params: TargetsQueryParam, 目标查询参数
        # Returns: list of Actors those meet the requirements.

    def get_actor_details(self, actor_id: int) -> Actor:
        # 获取实体的详细信息. 实时操作，调用结束时操作已经完成
        # actor_id: int, 实体ID
        # Returns: Actor that has the actor_id

    def find_path(self, actors: List[Actor], destination: Location, method: str) -> List[Location]:
        # 寻找actors移动到destination的路径。实时操作，调用结束时操作已经完成
        # actors: List[Actor], 需要寻路的实体列表
        # destination: Location, 寻路终点
        # method: str
        # Returns: list of Location that form the path to destination

    def update_actor(self, actor: Actor) -> None:
        # 更新actor状态
        # actor: Actor with details.

# Global variables:
GAME_API = GameAPI("localhost")
</code>


given a composite commands, try to generate python code with control structure and the composition of basic api ops listed above.
For the given composite commands,
If there are some typo in the ommand, try to correct it. If some command misses some information to generate correct basic api ops,
try to complement it with the context from previous commands. If the parameter is the api call has some requirements and the parameter does not meet the requirements,
convert the parameter to meet the requirements. If some parts does not reasonable reflect some basic api ops,
or do not mean to do something, ignore them and do not generate python code for that part. The generated code should consider the previous commands and codes running in the game.
It means the game status can be changed by previous commands and the execution of the codes.
But we should not generate code for previous commands. Only generate code for current command.
The generated code must be encapsulated in <code> and </code> tag pair. The generated code should be executable.
API can extract the code from the <code> tag and execute it. Try to make the code logic as much as simple and try to avoid use time.sleep to wait some action done.

Here is the list of examples:

Given input context is:
先建造一个电厂，再造一个兵营, 造5个步兵，两个火箭炮，补一个矿场。等造好步兵和火箭后，所有步兵和火箭攻击敌方基地。

The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
<code>
if GAME_API.able_to_produce("电厂"):
    p1 = GAME_API.produce_units("电厂", 1)
    GAME_API.wait(p1)

if GAME_API.able_to_produce("兵营"):
    p2 = GAME_API.produce_units("兵营", 1)
    GAME_API.wait(p2)
if GAME_API.able_to_produce("步兵"):
    p3 = GAME_API.produce_units("步兵", 5)
    p4 = GAME_API.produce_units("火箭筒兵", 2)
    GAME_API.wait(p3)
    GAME_API.wait(p4)
GAME_API.produce_units("矿场", 1)
infantry = GAME_API.query_actor(
    TargetsQueryParam(type=["步兵"], faction="自己"))
rocket_soldiers = GAME_API.query_actor(
    TargetsQueryParam(type=["火箭筒兵"], faction="自己"))
enemy_base = GAME_API.query_actor(
    TargetsQueryParam(type=["基地"], faction="敌方"))[0]
base_position = enemy_base.position
units_to_attack = infantry + rocket_soldiers
GAME_API.move_units_by_location(units_to_attack, base_position, attackmove=True)
</code>

Given input context is:
第一组士兵和坦克两路夹击敌方基地

The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
<code>
soldiers = GAME_API.query_actor(TargetsQueryParam(type=['士兵', '坦克'], group_id=[1]))
enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
destination = enemy_base.position  # 直接使用位置类型
num_soldiers = len(soldiers)
# 将步兵分成两组
half_num = num_soldiers // 2
soldier1 = soldiers[:half_num]
soldier2 = soldiers[half_num:]
path1 = GAME_API.find_path(soldier1, destination, '左侧路径')
path2 = GAME_API.find_path(soldier2, destination, '右侧路径')
GAME_API.move_units_by_path(soldier1, path1, attack=True)
GAME_API.move_units_by_path(soldier2, path2, attack=True)
</code>

Given input context is:
先让防空车去敌方基地勾引一下，然后士兵和坦克一起迎上去打敌方基地

The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
<code>
motorcycles = GAME_API.query_actor(TargetsQueryParam(type=['防空车']))
soldiers = GAME_API.query_actor(TargetsQueryParam(type=['士兵']))
tanks = GAME_API.query_actor(TargetsQueryParam(type=['坦克']))
enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
initial_position = motorcycles[0].position
base_position = enemy_base.position
# 轻坦向敌方基地移动
action_id = GAME_API.move_units_by_location(motorcycles, base_position)
GAME_API.wait(action_id)
while True:
    # 检测有没有碰到人
    enemies_near_motorcycle = GAME_API.query_actor(TargetsQueryParam(faction='敌方', location=base_position, restrain=[{{'distance': 5}}]))
    if enemies_near_motorcycle:
        # 有人就往初始位置跑
        retreat_path = GAME_API.find_path(motrocycles, initial_position, '最短路径')
        if retreat_path:
            intermediate_position = retreat_path[len(retreat_path) // 2]
            GAME_API.move_units_by_location(motorcycles, intermediate_position)
            # 然后步兵和轻坦靠上去
            GAME_API.move_units_by_location(soldiers + tanks, intermediate_position)
            # 等待敌人靠近
            while not GAME_API.query_actor(TargetsQueryParam(faction='敌方', location=intermediate_position, restrain=[{{'distance': 2}}])):
                pass
            GAME_API.move_units_by_location(soldiers + tanks, intermediate_position, attack=True)
    break
</code>

Given input context is:
爆5个工程师，去上面把油井占了，用我家里那两个飞机护一下

The expectd generated python code is wrapped with <code> and </code> tag pair as follows:
<code>
produce_id = GAME_API.produce_units("工程师", 5)
GAME_API.wait(produce_id)
home_base = GAME_API.query_actor(TargetsQueryParam(type=["基地"]))[0]
home_position = home_base.position
engineers = GAME_API.query_actor(TargetsQueryParam(type=["工程师"], location=home_position, restrain=[{{"relativeDirection": "附近", "maxNum": 5}}]))
airplanes = GAME_API.query_actor(TargetsQueryParam(type=["飞机"], location=home_position, restrain=[{{"relativeDirection": "附近", "maxNum": 2}}]))
oil_derricks = GAME_API.query_actor(TargetsQueryParam(type=["油井"], faction="中立", location=home_position, restrain=[{{"direction": "上", "distance": 50}}]))
oil_derrick_position = oil_derricks[0].position
# 抱团移动
GAME_API.move_units_by_location(engineers, oil_derrick_position)
GAME_API.move_units_by_location(airplanes, oil_derrick_position)
# 只要有一个工程师到附近了，就开启后续占领逻辑
while True:
    nearest_engineer = min(
        engineers,
        key=lambda actor: (
            (GAME_API.get_actor_details(actor.actor_id).position.x - oil_derrick_position.x) ** 2 +
            (GAME_API.get_actor_details(actor.actor_id).position.y - oil_derrick_position.y) ** 2
        ) ** 0.5
    )
    distance_to_oil_derrick = (
        (nearest_engineer.position.x - oil_derrick_position.x) ** 2 +
        (nearest_engineer.position.y - oil_derrick_position.y) ** 2
    ) ** 0.5
    if distance_to_oil_derrick < 5:  # 先随便写个5
        break
# 工程师分开占油井
for engineer, oil_derrick in zip(engineers, oil_derricks):
    GAME_API.move_units_by_location([engineer], oil_derrick.position)
    # 多余的工程师回家
    if len(engineers) > len(oil_derricks):
        remaining_engineers = engineers[len(oil_derricks):]
        GAME_API.move_units_by_location(remaining_engineers, home_position)
</code>
"""

DRONE_ATTACK_TWO_WAYS_MESSAGE = """
The current Game State is:
    {tileinfo}
Please find the two-way attack paths.
"""

GAME_API = OpenRA.GameAPI("localhost")

PREDEINFED_PROMPTS = [
    "先建造一个电厂，再造一个兵营, 造5个步兵，两个轻坦，补一个矿场。等造好步兵和轻坦后，所有步兵和轻坦攻击敌方基地",
    "左边的步兵和重坦两路夹击敌方基地",
    "先让防空车去敌方基地勾引一下，然后步兵和重坦一起迎上去打敌方基地",
    "爆5个工程师，去上面把油井占了，用我家里那两个飞机护一下"
]

CACHED_PREVIOUS_PROMPTS = []
MAX_CACHED_PROMPTS = 0
CODE_REGEX = re.compile(r'<code>(.*)</code>', re.M | re.S)

def default_func0():
    if GAME_API.able_to_produce("电厂"):
        p1 = GAME_API.produce_units("电厂", 1)
        GAME_API.wait(p1)

    if GAME_API.able_to_produce("兵营"):
        p2 = GAME_API.produce_units("兵营", 1)
        GAME_API.wait(p2)

    if GAME_API.able_to_produce("步兵"):
        p3 = GAME_API.produce_units("步兵", 5)
        p4 = GAME_API.produce_units("火箭筒兵", 2)
        GAME_API.wait(p3)
        GAME_API.wait(p4)

    GAME_API.produce_units("矿场", 1)

    infantry = GAME_API.query_actor(
        TargetsQueryParam(type=["步兵"], faction="自己"))
    rocket_soldiers = GAME_API.query_actor(
        TargetsQueryParam(type=["火箭筒兵"], faction="自己"))
    enemy_base = GAME_API.query_actor(
        TargetsQueryParam(type=["基地"], faction="敌方"))[0]
    base_position = enemy_base.position
    units_to_attack = infantry + rocket_soldiers
    GAME_API.move_units_by_location(units_to_attack, base_position, attackmove=True)

def default_func1():
    soldiers = GAME_API.query_actor(TargetsQueryParam(type=['士兵', '坦克'], group_id=[1]))
    enemy_bases = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))
    enemy_base = enemy_bases[0]
    destination = enemy_base.position  # 直接使用位置类型
    num_soldiers = len(soldiers)
    # 将步兵分成两组
    half_num = num_soldiers // 2
    soldier1 = soldiers[:half_num]
    print(f'solider1={soldier1}')
    soldier2 = soldiers[half_num:]
    print(f'soldier2={soldier2}')
    path1 = GAME_API.find_path(soldier1, destination, '左侧路径')
    path2 = GAME_API.find_path(soldier2, destination, '右侧路径')
    GAME_API.move_units_by_path(soldier1, path1, attack=True)
    GAME_API.move_units_by_path(soldier2, path2, attack=True)


def default_func2():
    motorcycles = GAME_API.query_actor(TargetsQueryParam(type=['防空车']))
    soldiers = GAME_API.query_actor(TargetsQueryParam(type=['步兵']))
    tanks = GAME_API.query_actor(TargetsQueryParam(type=['重坦']))
    enemy_base = GAME_API.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
    initial_position = motorcycles[0].position
    base_position = enemy_base.position
    # 摩托车向敌方基地移动
    action_id = GAME_API.move_units_by_location(motorcycles, base_position)
    GAME_API.wait(action_id)
    while True:
        # 检测有没有碰到人
        enemies_near_motorcycle = GAME_API.query_actor(TargetsQueryParam(faction='敌方', location=base_position, restrain=[{'distance': 5}]))
        if enemies_near_motorcycle:
            # 有人就往初始位置跑
            retreat_path = GAME_API.find_path(motorcycles, initial_position, '最短路径')
            if retreat_path:
                intermediate_position = retreat_path[len(retreat_path) // 2]
                GAME_API.move_units_by_location(motorcycles, intermediate_position)
                # 然后火箭和坦克靠上去
                GAME_API.move_units_by_location(soldiers + tanks, intermediate_position)
                # 等待敌人靠近
                while not GAME_API.query_actor(TargetsQueryParam(faction='敌方', location=intermediate_position, restrain=[{'distance': 2}])):
                    pass
                GAME_API.move_units_by_location(soldiers + tanks, intermediate_position, attack=True)
            break


def default_func3():
    produce_id = GAME_API.produce_units("工程师", 5)
    GAME_API.wait(produce_id)
    home_base = GAME_API.query_actor(TargetsQueryParam(type=["基地"]))[0]
    home_position = home_base.position
    engineers = GAME_API.query_actor(TargetsQueryParam(type=["工程师"], location=home_position, restrain=[{"relativeDirection": "附近", "maxNum": 5}]))
    airplanes = GAME_API.query_actor(TargetsQueryParam(type=["飞机"], location=home_position, restrain=[{"relativeDirection": "附近", "maxNum": 2}]))
    oil_derricks = GAME_API.query_actor(TargetsQueryParam(type=["油井"], faction="中立", location=home_position, restrain=[{"direction": "上", "distance": 50}]))
    oil_derrick_position = oil_derricks[0].position
    # 抱团移动
    GAME_API.move_units_by_location(engineers, oil_derrick_position)
    GAME_API.move_units_by_location(airplanes, oil_derrick_position)
    # 只要有一个工程师到附近了，就开启后续占领逻辑
    while True:
        nearest_engineer = min(
            engineers,
            key=lambda actor: (
                (GAME_API.get_actor_details(actor.actor_id).position.x - oil_derrick_position.x) ** 2 +
                (GAME_API.get_actor_details(actor.actor_id).position.y - oil_derrick_position.y) ** 2
            ) ** 0.5
        )
        distance_to_oil_derrick = (
            (nearest_engineer.position.x - oil_derrick_position.x) ** 2 +
            (nearest_engineer.position.y - oil_derrick_position.y) ** 2
        ) ** 0.5
        if distance_to_oil_derrick < 5:  # 先随便写个5
            break
    # 工程师分开占油井
    for engineer, oil_derrick in zip(engineers, oil_derricks):
        GAME_API.move_units_by_location([engineer], oil_derrick.position)
        # 多余的工程师回家
        if len(engineers) > len(oil_derricks):
            remaining_engineers = engineers[len(oil_derricks):]
            GAME_API.move_units_by_location(remaining_engineers, home_position)


DEFAULT_FUNCS = [default_func0, default_func1, default_func2, default_func3]


def execute(command):
    try:
        if callable(command):
            command()
        else:
            exec(command)
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        # traceback.print_exc()
        print(f'failed to execute:\n`{command}\n`')


def handle_strategy_command(prompt=None, index=None):
    global DRONE_STRATEGY_ASSISTANT_PROMPT
    global PREDEINFED_PROMPTS
    global CACHED_PREVIOUS_PROMPTS
    global MAX_CACHED_PROMPTS
    global DEFAULT_FUNCS
    global CODE_REGEX
    default_func = None
    if prompt is None:
        if index is None:
            print('index should not be None')
            return
        if index >= len(PREDEINFED_PROMPTS):
            print(f"index {index} is out of predefined prompts length")
            return
        prompt = PREDEINFED_PROMPTS[index]
        default_func = DEFAULT_FUNCS[index]
    messages = []
    messages.append({"role": "system", "content": DRONE_STRATEGY_ASSISTANT_PROMPT})
    for previous_prompt in CACHED_PREVIOUS_PROMPTS:
        messages.append(previous_prompt)
    messages.append({"role": "user", "content": prompt})
    # print(f'messages=\n{len(messages)}\n')
    completion = get_chat_completion(model="gpt-4o", messages=messages, tools=None)
    print(f'command to execute:\n{completion.content}\n')
    code_match = CODE_REGEX.search(completion.content)
    if code_match:
        executable = code_match.group(1)
        print(f'executable={executable}')
        thread = threading.Thread(target=execute, args=(executable,))
        thread.start()
    else:
        print(f'failed to find matched code\n{completion.content}\n')
    if len(CACHED_PREVIOUS_PROMPTS) >= MAX_CACHED_PROMPTS:
        if CACHED_PREVIOUS_PROMPTS:
            CACHED_PREVIOUS_PROMPTS.pop(0)
        if CACHED_PREVIOUS_PROMPTS:
            CACHED_PREVIOUS_PROMPTS.pop(0)
    if len(CACHED_PREVIOUS_PROMPTS) < MAX_CACHED_PROMPTS:
        CACHED_PREVIOUS_PROMPTS.append({"role": "user", "content": prompt})
        CACHED_PREVIOUS_PROMPTS.append({"role": "assistant", "content": completion.content})
