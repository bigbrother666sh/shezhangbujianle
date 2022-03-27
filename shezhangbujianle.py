import os
import sys

sys.path.append(os.path.abspath(os.curdir))
import re
import json
import time
from inspurai import Yuan, set_yuan_account, Example
import asyncio
import paddlehub as hub
from wechaty import (
    Contact,
    Message,
    Wechaty,
    MessageType,
    #Room,
)

set_yuan_account("", "") #这里填入你自己的浪潮源API账号，申请地址https://air.inspur.com/home

# check1 = hub.Module(name="porn_detection_lstm")  #色情检测模型
# check = hub.Module(name="ernie-csc")  # 错别字、病句自动更正模型
simnet_bow = hub.Module(name="simnet_bow")

director = 'wxid_a6xxa7n11u5j22'  #填入导演账号对于机器人帐号的微信UUID
with open('users.json') as f:
    users = json.load(f)

rooms = []

# 读取example语料
data = []
with open("TM.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("tanming examples loaded successfully")

with open("KM.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("kongmo examples loaded successfully")

with open("LC.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Lichao examples loaded successfully")

with open("SR.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Sunruo examples loaded successfully")

names = ["谭明", "孔墨", "李超", "孙若"]
# 记忆机制
memory = {"tm": [], "km": [], "lc": [], "sr": []}
# 群聊中触发AI活跃的关键词
activity = ["蔡晓", "大家说", "晓晓", "大家怎么", "咱们说", "咱们怎么"]
talker_dict = {}


def soul(text, a, b):
    who = names[a]
    lines = data[a]
    yuan = Yuan(input_prefix="对话，",
                input_suffix="",
                output_prefix="蔡晓说：“",
                output_suffix="”",
                append_output_prefix_to_query=True)
    test_text_1 = []
    test_text_2 = []

    for i in range(0, len(lines), 2):
        test_text_1.append(lines[i].strip('\n'))
        test_text_2.append(text)

    test_text = [test_text_1, test_text_2]
    results = simnet_bow.similarity(texts=test_text, use_gpu=True)
    results.sort(key=lambda k: (k.get('similarity')), reverse=True)
    print("example load---top-3 similarity：", results[0]['similarity'], "，", results[1]['similarity'], "，",
          results[2]['similarity'])
    yuan.add_example(
        Example(inp=who + "说：“" + results[0]['text_1'] + "”",
                out=lines[lines.index(results[0]['text_1'] + '\n') + 1].strip('\n')))
    if results[1]['similarity'] > 0.75:
        yuan.add_example(
            Example(inp=who + "说：“" + results[1]['text_1'] + "”",
                    out=lines[lines.index(results[1]['text_1'] + '\n') + 1].strip('\n')))
    if results[2]['similarity'] > 0.75:
        yuan.add_example(
            Example(inp=who + "说：“" + results[2]['text_1'] + "”",
                    out=lines[lines.index(results[2]['text_1'] + '\n') + 1].strip('\n')))
    time.sleep(1)
    print(memory[b])
    reply = yuan.submit_API(''.join(memory[b]), trun="”")
    with open(who + ".txt", 'a', encoding='utf-8') as f:
        f.write(who + ":" + text + "---top-3 similarity：" + str(results[0]['similarity']) + "，" + str(
            results[1]['similarity']) + "，" + str(results[2]['similarity']) + "\n")
        f.write(reply + "\n")
    return reply


async def on_message(msg: Message):
    """
    Message Handler for the Bot
    """
    global rooms

    if msg.is_self() or msg.type() != MessageType.MESSAGE_TYPE_TEXT:
        return
    talker = msg.talker()

    if msg.text() == '这是谭明':
        users['tanming'] = talker.contact_id
        talker_dict['tm'] = talker
        print("tanming has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return
    if msg.text() == '这是孔墨':
        users['kongmo'] = talker.contact_id
        talker_dict['km'] = talker
        print("kongmo has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return
    if msg.text() == '这是李超':
        users['lichao'] = talker.contact_id
        talker_dict['lc'] = talker
        print("lichao has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return
    if msg.text() == '这是孙若':
        users['sunruo'] = talker.contact_id
        talker_dict['sr'] = talker
        print("sunruo has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return

    if talker.contact_id == director:
        text = msg.text()
        if text[:2] == 'zc':
            if text[2:4] == 'tm':
                users['tanming'] = text[4:]
            if text[2:4] == 'km':
                users['kongmo'] = text[4:]
            if text[2:4] == 'lc':
                users['lichao'] = text[4:]
            if text[2:4] == 'sr':
                users['sunruo'] = text[4:]
            print("users registed updated, the latest users list is:", users)
        # 代码1，存储当场用户，在本场所有玩家注册后，必须执行这一步，期间有必要程序关闭或重启就不会丢失用户信息
        if text == '1':
            with open('users.json', 'w') as f:
                json.dump(users, f)
            print("users dict has been saved as bigbro/users.jason")

        # 主动消息（必须符合前置条件，否则会报错，且只限大群和私聊）
        if text == "欢迎各位，我是本场游戏导演，下面我来宣布游戏规则，请各位务必遵守":  # 欢迎语注册房间
            talker_dict["rm"] = msg.room()
        if text == 'jieshu':
            await talker_dict["rm"].say("你们很聪明，但可惜，一切都已经晚了，事情已经开始，你们谁也逃不掉!")
            await talker_dict["sr"].say("父亲的计划已经成功，欢迎你加入我们并成为我们未来的主宰。asyncio.run(main())")
        if text == "qun":
            await talker_dict["rm"].say("大家要么发表下各自的意见啊？")
        if text == "tanming":
            await talker_dict["tm"].say("我就跟他们说新程序会有问题，这下出事了吧？……先不管这个了，你接下来打算怎么办？我会配合你的。")
        if text == "kongmo":
            await talker_dict["km"].say("孔墨小朋友，让我来告诉你一个秘密，有了脑机接口，你就可以直接用意识操控手机，打王者可爽了……[阴险]")
        if text == "lichao":
            await talker_dict["lc"].say("小朋友，千万不要相信陌生人发来的短信哦……[微笑]")
        if text == "sunruo":
            await talker_dict["sr"].say("早啊~今天星期几来着……")
        # 预设回答，2+tm+zhangjiayi格式
        if text[0] == '2':
            with open('caixiao.json', encoding='utf-8') as f:
                answers = json.load(f)
            await talker_dict[text[1:3]].say(answers[text[3:]])

        # 代码yw 记忆遗忘机制，当出现重复回复的时候使用，无法区分群聊，rm会遗忘所有群聊记忆
        if text[:2] == 'yw':
            if text[2:4] == 'tm':
                memory['tm'] = []
            if text[2:4] == 'km':
                memory['km'] = []
            if text[2:4] == 'lc':
                memory['lc'] = []
            if text[2:4] == 'sr':
                memory['sr'] = []
            if text[2:4] == 'rm':
                rooms = []
            print(text[2:4] + "'s memory has been forgiven")
        return

    if talker.contact_id == users['tanming']:
        # talker_dict['tanming'] = talker
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id] = []
            # if len(re.sub(r'\s', "",re.sub(r'@.+?\s', "", msg.text())))==0:
            for key in activity:
                if key in msg.text():
                    print("tanming called in the room, reply generating...")
                    text = re.sub(r'\s', "，", msg.text())
                    text = text.replace("@", "").replace("#", "号").replace("&", "和")
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("谭明说：“" + text + "”")
                    reply = soul(text, 0, msg.room().room_id)
                    await msg.room().say(reply)
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
                    return
        else:
            print("tanming called privately, reply generating...")
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("#", "号").replace("&", "和")
            if len(memory["tm"]) > 2:
                memory["tm"].pop(0)
            memory["tm"].append("谭明说：“" + text + "”")
            reply = soul(text, 0, "tm")
            await talker.say(reply)
            if len(memory["tm"]) > 2:
                memory["tm"].pop(0)
            memory["tm"].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
        return

    if talker.contact_id == users['kongmo']:
        # talker_dict['kongmo'] = talker
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id] = []
            for key in activity:
                if key in msg.text():
                    print("kongmo called in the room, reply generating...")
                    text = re.sub(r'\s', "，", msg.text())
                    text = text.replace("@", "").replace("#", "号").replace("&", "和")
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("孔墨说：“" + text + "”")
                    reply = soul(text, 0, msg.room().room_id)
                    await msg.room().say(reply)
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
                    return
        else:
            print("kongmo called privately, reply generating...")
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("#", "号").replace("&", "和")
            if len(memory["km"]) > 2:
                memory["km"].pop(0)
            memory["km"].append("孔墨说：“" + text + "”")
            reply = soul(text, 1, "km")
            await talker.say(reply)
            if len(memory["km"]) > 2:
                memory["km"].pop(0)
            memory["km"].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
        return

    if talker.contact_id == users['lichao']:
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id] = []
            for key in activity:
                if key in msg.text():
                    print("lichao called in the room, reply generating...")
                    text = re.sub(r'\s', "，", msg.text())
                    text = text.replace("@", "").replace("#", "号").replace("&", "和")
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("李超说：“" + text + "”")
                    reply = soul(text, 0, msg.room().room_id)
                    await msg.room().say(reply)
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
                    return
        else:
            print("lichao called privately, reply generating...")
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("#", "号").replace("&", "和")
            if len(memory["lc"]) > 2:
                memory["lc"].pop(0)
            memory["lc"].append("李超说：“" + text + "”")
            reply = soul(text, 2, "lc")
            await talker.say(reply)
            if len(memory["lc"]) > 2:
                memory["lc"].pop(0)
            memory["lc"].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
        return

    if talker.contact_id == users['sunruo']:
        # talker_dict['sunruo'] = talker
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id] = []
            for key in activity:
                if key in msg.text():
                    print("sunruo called in the room, reply generating...")
                    text = re.sub(r'\s', "，", msg.text())
                    text = text.replace("@", "").replace("#", "号").replace("&", "和")
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("孙若说：“" + text + "”")
                    reply = soul(text, 0, msg.room().room_id)
                    await msg.room().say(reply)
                    if len(memory[msg.room().room_id]) > 2:
                        memory[msg.room().room_id].pop(0)
                    memory[msg.room().room_id].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
                    return
        else:
            print("sunruo called privately, reply generating...")
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("#", "号").replace("&", "和")
            if len(memory["sr"]) > 2:
                memory["sr"].pop(0)
            memory["sr"].append("孙若说：“" + text + "”")
            reply = soul(text, 3, "sr")
            await talker.say(reply)
            if len(memory["sr"]) > 2:
                memory["sr"].pop(0)
            memory["sr"].append("蔡晓说：“" + reply.replace("#", "").replace("&", "") + "”")
        return


async def on_login(user: Contact):
    """
    Login Handler for the Bot
    """
    print(user)


async def main():
    """
    Async Main Entry
    """

    if 'WECHATY_PUPPET_SERVICE_TOKEN' not in os.environ:
        print('''
            Error: WECHATY_PUPPET_SERVICE_TOKEN is not found in the environment variables
            You need a TOKEN to run the Python Wechaty. Please goto our README for details
            https://github.com/wechaty/python-wechaty-getting-started/#wechaty_puppet_service_token
        ''')

    xiaoyan = Wechaty()

    # bot.on('scan',      on_scan)
    xiaoyan.on('login', on_login)
    xiaoyan.on('message', on_message)
    # bot.on('friendship', on_request)

    await xiaoyan.start()

    print('[Python Wechaty] xiaoyan started.')


asyncio.run(main())

"""
code reference:
Python Wechaty geeting started- https://github.com/wechaty/python-wechaty-getting-started/
Yuan1.0 API - https://github.com/Shawn-Inspur/Yuan-1.0
Paddlehub - https://github.com/PaddlePaddle/PaddleHub
    
Author:    bigbrother666  <https://github.com/bigbrother666sh>
2022 @ Copyright Wechaty Contributors <https://github.com/wechaty>
Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
