
import contextlib
import os
import sys
import yaml
import re
from typing import Optional, List, Dict, Any
import threading
import traceback
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import platform


# from openai import client
from openai import OpenAI
CLIENT = OpenAI()

start_time = time.perf_counter()

log_directory = "Logs"
os.makedirs(log_directory, exist_ok=True)

device_name = platform.node()
current_time = datetime.now().strftime("%Y%m%d%H%M%S")

prompt_path = os.path.join("./prompt", device_name, current_time)
prompt_counter = 0


def save_prompt(static_prompt: str, dynamic_prompt: str, player_prompt: str, answer: str):
    global prompt_counter

    if prompt_counter == 0:
        os.makedirs(prompt_path, exist_ok=True)

    prompt_counter += 1

    base_file_prefix = os.path.join(prompt_path, f"{device_name}_{current_time}_{prompt_counter}")
    base_file_suffix = ".txt"

    with open(base_file_prefix + 'static_prompt'+base_file_suffix, 'w', encoding='utf-8') as file:
        file.write(static_prompt)
    with open(base_file_prefix + 'dynamic_prompt'+base_file_suffix, 'w', encoding='utf-8') as file:
        file.write(dynamic_prompt)
    with open(base_file_prefix + 'player_prompt'+base_file_suffix, 'w', encoding='utf-8') as file:
        file.write(player_prompt)
    with open(base_file_prefix + 'answer'+base_file_suffix, 'w', encoding='utf-8') as file:
        file.write(answer)


log_filename = os.path.join(log_directory, f"{current_time}.log")


def print_log(content):
    elapsed_time = time.perf_counter() - start_time
    formatted_elapsed_time = f"{elapsed_time:.2f}"

    log_entry = f"COPILOT LOG{formatted_elapsed_time}: {content}\n"

    with open(log_filename, "a", encoding='utf-8') as log_file:
        log_file.write(log_entry)


def get_chat_completion(
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
    max_tokens=1500,
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


MEMORY = "无"

api = OpenRA.GameAPI("localhost")


def make_sys_prompt(no_sample_prompt=False):

    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    ALL_ACTORS = config['ALL_ACTORS']
    ALL_DIRECTIONS = config['ALL_DIRECTIONS']
    ALL_GROUPS = config['ALL_GROUPS']
    ALL_REGIONS = config['ALL_REGIONS']
    ALL_RELATIVES = config['ALL_RELATIVES']
    ALL_BUILDINGS = config['ALL_BUILDINGS']
    ALL_DEFENSE_DEVICES = config['ALL_DEFENSE_DEVICES']
    ALL_INFANTRIES = config['ALL_INFANTRIES']
    ALL_TANKS = config['ALL_TANKS']

    # 合并 ALL_MOVABLES 和 ALL_UNITS
    ALL_MOVABLES = ALL_INFANTRIES + ALL_TANKS
    ALL_UNITS = ALL_BUILDINGS + ALL_DEFENSE_DEVICES + ALL_MOVABLES

    gamelib_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../OpenRA_Copilot_Library'))
    api_path = os.path.join(gamelib_dir, 'game_api.py')
    api_struct_path = os.path.join(gamelib_dir, 'models.py')
    with open(api_path, 'r', encoding='utf-8') as file:
        api_content = file.read()
    with open(api_struct_path, 'r', encoding='utf-8') as file:
        api_struct_content = file.read()

    sample_code = ""
    if not no_sample_prompt:
        sample_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../Samples'))
        sample_index = 1

        for filename in os.listdir(sample_dir):
            print(f"SampleFileName:{filename}")
            if filename.endswith('.py'):
                file_path = os.path.join(sample_dir, filename)

                with open(file_path, 'r', encoding='utf-8') as file:
                    first_line = file.readline().strip()
                    if first_line == "# COPILOT_PROMPT_IGNORE":
                        print(f"Skipping {filename} due to ignore mark.")
                    code_content = file.read()

                sample_code += f"{sample_index}.{filename}\n<code>{code_content}</code>\n\n"
                sample_index += 1

    current_time = time.perf_counter() - start_time
    formatted_time = f"{current_time:.2f}"

    playerbaseinfo = api.player_base_info_query()

    visible_units = api.query_actor(
        TargetsQueryParam(
            type=[],  # 查询所有类型的单位
            faction=["任意"],  # 查询所有阵营的单位
            range="screen",  # 查询屏幕范围内的单位
            restrain=[{"visible": True}]  # 必须可见
        )
    )
    screen_units_str = ""
    for unit in visible_units:
        screen_units_str += (
            f"单位ID={unit.actor_id}, 阵营= {unit.faction}, 类型={unit.type}"
            f", 位置=({unit.position.x}, {unit.position.y})\n"
        )

    static_prompt = f"""
你是 OpenRA（红色警戒）游戏的战略AI指挥副官。你需要根据玩家的指示来辅助玩家进行游戏，具体来说，你需要输出python代码，使用python的OpenRA库与游戏交互，我们会执行你输出的代码

prompt将分为6个部分：
1.python 库相关内容，包括数据结构，api以及一些sample code
2.当前正在执行的内容，这些都是正在运行的，你之前的代码
3.你和玩家之前的历史对话
4.你的记忆
5.目前游戏的基本信息
6.当前的时间戳，RTS游戏是有很强时效性的

你的输出也要分为4个部分：
1.<code> 可执行的python代码 </code>
2.<speech> 你对玩家说的话，包括解释你做了什么，以及为什么，这一部分对玩家可见，会用语音给玩家播放 </speech>
3.<title> 你正在运行的内容的标题，应该简洁明了，这个是给你自己看的 </title>
4.<memory> 你新的记忆，筛去无用部分，根据新的内容修改，可以参考时间戳来决定 </memory>

注意，不同部分需要用不同的尖括号框起来

prompt part 1:python 库相关内容，包括数据结构，api以及一些sample code

以下是参数列表：
ALL_ACTORS = {ALL_ACTORS}
ALL_DIRECTIONS = {ALL_DIRECTIONS}
ALL_GROUPS = {ALL_GROUPS}
ALL_REGIONS = {ALL_REGIONS}
ALL_RELATIVES = {ALL_RELATIVES}
ALL_BUILDINGS = {ALL_BUILDINGS}
ALL_UNITS = {ALL_UNITS}

接口如下所示： api_struct: <code> {api_struct_content} </code> api_define: <code> {api_content} </code>

给定一个复合命令，尝试使用以上列出的基本 API 操作组合生成带有控制结构的 Python 代码，遇到意料外的情况，可以用raise报错

对于给定的复合命令： 如果命令中存在拼写错误，请尝试修正。如果某个命令缺少生成正确基本 API 操作所需的信息，请尝试从先前的命令中补充这些信息。如果参数在 API 调用中有一些要求，但该参数不满足要求，请将参数转换为满足要求的格式。如果某些部分没有合理地反映某些基本 API 操作，或者没有实际意义，请忽略这些部分，不为它们生成 Python 代码。生成的代码应考虑先前的命令和在游戏中运行的代码。这意味着游戏状态可能会因先前的命令和代码的执行而改变。但我们不应该为先前的命令生成代码，只为当前命令生成代码。

生成的代码必须封装在 <code> 和 </code> 标签对中。生成的代码应当是可执行的。API 可以从 <code> 标签中提取代码并执行。尝试使代码逻辑尽可能简单，并尽量避免使用 time.sleep 来等待某些操作完成。

{' ' if no_sample_prompt else '以下是一些示例代码：' + sample_code}"""
    dynamic_prompt = f"""
prompt part 2:当前正在执行的内容，这些都是正在运行的，你之前的代码
无
prompt part 3:你和玩家之前的历史对话
无
prompt part 4:你的记忆
{MEMORY}
prompt part 5:目前游戏的基本信息
玩家持有资源：{playerbaseinfo.Cash + playerbaseinfo.Resources}
玩家当前剩余电力：{playerbaseinfo.Power}
屏幕内单位：\n{screen_units_str}
prompt part 6:当前的时间戳
当前是运行的第："{formatted_time}"秒
    """
    prompt = static_prompt + dynamic_prompt
    print_log(f"prompt:\n{prompt}\n")
    return static_prompt, dynamic_prompt


CACHED_PREVIOUS_PROMPTS = []
MAX_CACHED_PROMPTS = 2


def create_tag_regex(tag_name):
    return re.compile(rf'<{tag_name}>(.*?)</{tag_name}>', re.M | re.S)


CODE_REGEX = create_tag_regex('code')
CODE_REGEX2 = re.compile(r'```python(.*)```', re.M | re.S)
SPEECH_REGEX = create_tag_regex('speech')
TITLE_REGEX = create_tag_regex('title')
MEMORY_REGEX = create_tag_regex('memory')


executor = ThreadPoolExecutor(max_workers=10)


def handle_strategy_command(prompt=None, model="gpt-4o", gui=None, no_sample_prompt=False):
    global CACHED_PREVIOUS_PROMPTS
    global MAX_CACHED_PROMPTS
    global CODE_REGEX
    global MEMORY
    default_func = None
    if prompt is None:
        print('prompt should not be None')
        print_log('prompt should not be None')
        return
    messages = []
    static_sys_prompt, dynamic_sys_prompt = make_sys_prompt(no_sample_prompt)
    messages.append(
        {"role": "system", "content": static_sys_prompt + dynamic_sys_prompt})
    for previous_prompt in CACHED_PREVIOUS_PROMPTS:
        messages.append(previous_prompt)
    messages.append({"role": "user", "content": prompt})

    print_log(f'Full Promt:\n{messages}\n')
    completion = get_chat_completion(
        model=model, messages=messages, tools=None)

    print(f'Response:\n{completion.content}\n')
    print_log(f'Response:\n{completion.content}\n')

    code_match = CODE_REGEX.search(completion.content)

    if code_match:
        executable = code_match.group(1)
    else:
        code_match = CODE_REGEX2.search(completion.content)

    mermory_match = MEMORY_REGEX.search(completion.content)
    if mermory_match:
        MEMORY = mermory_match.group(1)
        print_log(f'New Mermory:\n{MEMORY}\n')

    plan = None
    if gui:
        title_match = TITLE_REGEX.search(completion.content)
        speech_match = SPEECH_REGEX.search(completion.content)
        if speech_match:
            gui.add_ai_dialog(speech_match.group(1))
        if title_match:
            plan = gui.add_plan_item(
                plan_name=title_match.group(1), status="进行中")
        if mermory_match:
            gui.set_memory_content(MEMORY)

    if code_match:

        save_prompt(static_sys_prompt, dynamic_sys_prompt, prompt, completion.content)

        executable = code_match.group(1)
        print(f'executable={executable}')
        print_log(f'executable={executable}')

        class GuiOutput:
            def __init__(self, gui):
                self.gui = gui

            def write(self, message):
                if message.strip():  # 忽略空行
                    self.gui.add_ai_dialog(message.strip(), False)

            def flush(self):
                pass

        def execute(command):
            try:
                captured_output = GuiOutput(gui)
                with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(captured_output):
                    if callable(command):
                        command()
                    else:
                        exec(command)
                    if gui and plan:
                        gui.update_plan_item_status(plan, "已完成")
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                traceback.print_exc()
                print(f'failed to execute:\n`{command}\n`')
                print_log(f'failed to execute:\n`{command}\n`')
                if gui and plan:
                    gui.update_plan_item_status(plan, "失败")
                    error_message = traceback.format_exception_only(type(e), e)
                    last_line = "".join(error_message).strip()
                    gui.add_ai_dialog(f"错误信息：{last_line}", False)

        future = executor.submit(execute, executable)
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


# 直接运行这个文件，这个文件会输出一个prompt，你可以直接复制到openai的playground里面进行测试
if __name__ == "__main__":
    prompt = make_sys_prompt()
    print(prompt)
