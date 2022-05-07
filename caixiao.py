import os
import sys
import time
sys.path.append(os.path.abspath(os.curdir))
#import re
import json
import datetime
from inspurai import Yuan, set_yuan_account, Example
import asyncio
import paddlehub as hub
from wechaty import (
    Contact,
    Message,
    Wechaty,
    MessageType,
    Room,
)

#这里填入你自己的浪潮源API账号，申请地址https://air.inspur.com/home
set_yuan_account("", "")
simnet_bow = hub.Module(name="simnet_bow")
bad_detection = hub.Module(name="porn_detection_lstm")

#填入导演账号对于机器人帐号的微信UUID
director = ["wxid_tnv0hd5hj3rs11", "wxid_a6xxa7n11u5j22"]
rooms = []
statement1 = "hey，先声明：您确认与我的对话不涉及任何隐私信息，相关的信息泄露风险均由您自行承担，同时您确认我们的对话是可以公开的，并且您本人承担由您发出的不当言论可能造成的法律风险。" \
            "如不接受请即刻停止对话，继续对话将被视为完全理解并接受上述声明。"
statement2 = "先声明：各位确认在本群中的对话不涉及任何隐私信息，相关的信息泄露风险均由信息发出方自行承担，同时各位确认本群对话是可以公开的，信息发出人将承担所有不当言论可能造成的法律风险。" \
            "如不接受请即刻退群，继续对话将被视为完全理解并接受上述声明。"

# 读取example语料
with open("cxzf.txt", 'r', encoding='utf-8') as f:
    data = [line for line in f.readlines() if line.strip()]
    print("examples loaded successfully")

# 记忆机制
memory = {}

def soul(text, memory_text):
    yuan = Yuan(engine='dialog',
                input_prefix="对话：“",
                input_suffix="”",
                output_prefix="答：“",
                output_suffix="”",
                append_output_prefix_to_query=True)

    test_text_1 = []
    test_text_2 = []

    for i in range(0, len(data), 2):
        test_text_1.append(data[i].strip('\n'))
        test_text_2.append(text)

    test_text = [test_text_1, test_text_2]
    results = simnet_bow.similarity(texts=test_text, use_gpu=True)
    results.sort(key=lambda k: (k.get('similarity')), reverse=True)

    for result in results:
        if result['similarity'] >= 0.88:
            yuan.add_example(
                Example(inp=result['text_1'], out=data[data.index(result['text_1'] + '\n') + 1].strip('\n')))
            print("example load---similarity：", result['similarity'])
        else:
            break

    if len(yuan.examples) == 0:
        print("no suitable example found---top-3 similarity：", results[0]['similarity'], "，", results[1]['similarity'], "，",
              results[2]['similarity'])

    while (1):
        time.sleep(1)
        reply = yuan.submit_API(''.join(memory_text)[4:], trun="”")
        if reply != memory_text[-1][4:-1]:
            if len(memory_text) > 1:
                if reply != memory_text[-2][3:-1]:
                    break
            else:
                break

    date = datetime.date.today().strftime("%d_%m_%Y")
    with open(date + ".txt", 'a', encoding='utf-8') as f:
        f.write("Q:" + text + "---top-3 similarity：" + str(results[0]['similarity']) + "，" + str(
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
    text = msg.text()
    id = talker.contact_id

    if text == '以上是打招呼的内容':
        await talker.say(statement1)
        return

    if id in director:
        if msg.room() and text == statement2:
            rooms.append(msg.room().room_id)
            return

        if text == '1':
            with open('rooms.json', 'w') as f:
                json.dump(rooms, f)
            print("rooms dict has been saved as bigbro/rooms.jason")
            return

    if msg.room():
        room = msg.room()
        if room.room_id not in rooms:
            return

        if not await msg.mention_self():
            return

        announce = await room.announce()
        if announce != statement2:
            owner = await room.owner()
            await room.say('请先设定群公告为隐私豁免声明', [owner.contact_id])
            return

        #id = talker.contact_id+msg.room().room_id
        text = await msg.mention_text()
        if len(text) == 0:
            await room.say("您能把话连起来说么，这样看着很累唉……", [talker.contact_id])
            return
        text = text.replace(r'\s', "，").replace("#", "号").replace("&", "和")
        bad_detection_result = bad_detection.detection(texts=[text], use_gpu=True, batch_size=1)

        if bad_detection_result[0]['porn_detection_label'] == 1:
            await room.say("请勿发表不当言论，您需要对您的言行负全部法律责任", [talker.contact_id])
            return

        if id not in memory.keys():
            memory[id] = ["对话：“" + text + "”"]
        else:
            if len(memory[id]) > 6:
                memory[id].pop(0)
            memory[id].append("对话：“" + text + "”")

        reply = soul(text, memory[id])
        if reply:
            await room.say(reply,[talker.contact_id])
        if len(memory[id]) > 6:
            memory[id].pop(0)
        memory[id].append("答：“" + reply + "”")

    else:
        text = text.replace(r'\s', "，").replace("#", "号").replace("&", "和")
        bad_detection_result = bad_detection.detection(texts=[text], use_gpu=True, batch_size=1)

        if bad_detection_result[0]['porn_detection_label'] == 1:
            await msg.say("请勿发表不当言论，您需要对您的言行负全部法律责任")
            return

        if id not in memory.keys():
            memory[id] = []
            await talker.say(statement1)
            return
        else:
            if len(memory[id]) > 6:
                memory[id].pop(0)
            memory[id].append("对话：“" + text + "”")

        reply = soul(text, memory[id])
        if reply:
            await talker.say(reply)
        if len(memory[id]) > 6:
            memory[id].pop(0)
        memory[id].append("答：“" + reply + "”")


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
2022 @ Copyright reseived
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
