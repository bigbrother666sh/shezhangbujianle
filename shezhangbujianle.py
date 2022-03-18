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
    # Room,
)

set_yuan_account("", "")  #填入对应的浪潮源1.0API账号,申请地址：https://air.inspur.com/home

# check1 = hub.Module(name="porn_detection_lstm")  #色情检测模型
check = hub.Module(name="ernie-csc")  # 错别字、病句自动更正模型
simnet_bow = hub.Module(name="simnet_bow")

director = 'wxid_a6xxa7n11u5j22'  #替换为导演的uuid
with open('users.json') as f:       #需要有一个初始的文件，可以用本项目提供的，第一轮游戏全部用户注册后，导演发指令存储下
    users = json.load(f)

talker_dict = {}
AI_ON = 0  # 设定为1的时候，关闭AI回复，此时机器人仅接受导演指令和初始化指令

# 读取example语料
data=[]
with open("TM0.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("tanming room examples loaded successfully")
with open("TM1.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("tanming private examples loaded successfully")
with open("KM0.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("kongmo room examples loaded successfully")
with open("KM1.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Kongmo private examples loaded successfully")
with open("LC0.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Lichao room examples loaded successfully")
with open("LC1.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Lichao private examples loaded successfully")
with open("SR0.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Sunruo room examples loaded successfully")
with open("SR1.txt", 'r', encoding='utf-8') as f:
    data.append([line for line in f.readlines() if line.strip()])
    print("Sunruo room examples loaded successfully")

names=["谭明","谭明","孔墨","孔墨","李超","李超","孙若","孙若"]
    

def soul(text, mark):
    who=names[mark]
    lines=data[mark]
    yuan = Yuan(input_prefix="对话，"+who+"问：“",
                input_suffix="”",
                output_prefix="蔡晓答：“",
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
    # print(results)
    yuan.add_example(
        Example(inp=results[0]['text_1'], out=lines[lines.index(results[0]['text_1'] + '\n') + 1].strip('\n')))
    if results[1]['similarity'] > 0.5:
        yuan.add_example(
            Example(inp=results[1]['text_1'], out=lines[lines.index(results[1]['text_1'] + '\n') + 1].strip('\n')))
    if results[2]['similarity'] > 0.5:
        yuan.add_example(
            Example(inp=results[2]['text_1'], out=lines[lines.index(results[2]['text_1'] + '\n') + 1].strip('\n')))
    time.sleep(1)
    reply = yuan.submit_API(text, trun="”")
    with open(who+str(mark)+".txt", 'a', encoding='utf-8') as f:
      f.write(who+":"+text+"---top-3 similarity："+str(results[0]['similarity'])+"，"+str(results[1]['similarity'])+"，"+str(results[2]['similarity'])+"\n")
      f.write(reply+"\n")
    return reply


async def on_message(msg: Message):
    """
    Message Handler for the Bot
    """
    global AI_ON
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
        if text[0] == '0':
            if text[1:3] == 'tm':
                users['tanming'] = text[3:]
            if text[1:3] == 'km':
                users['kongmo'] = text[3:]
            if text[1:3] == 'lc':
                users['lichao'] = text[3:]
            if text[1:3] == 'sr':
                users['sunruo'] = text[3:]
            print("users registed updated, the latest users list is:", users)

        # 1设置机器人静默（默认开启）
        if text == 'mute':
            AI_ON = 1
            print("AI has been muted")
        # 2机器人再次打开
        if text == 'aion':
            AI_ON = 0
            print("AI muted has been canceled")
        #   3保存用户设置( 应对游戏中程序需要重启的情况)
        if text == 'saveuser':
            with open('users.json', 'w') as f:
                json.dump(users, f)
            print("users dict has been saved as bigbro/users.jason")
        # 代码2开头，导演接入，实现主动发信息（todo群消息mention）
        if text=="欢迎各位，我是本场游戏导演，下面我来宣布游戏规则，请各位务必遵守":  #欢迎语注册房间
            talker_dict["rm"]=msg.room()
        if text[0]=='2':
            tosay=talker_dict[text[1:3]]
            if tosay:
                await tosay.say(text[3:])
            else:
                print(text[1:3]+"has not registed yet. can not send by director")

        return

    if AI_ON == 1:
        print("AI had been muted. Director send 'aion' to turn on again")
        return

    if talker.contact_id == users['tanming']:
        # talker_dict['tanming'] = talker
        if msg.room():
            if '@蔡晓' in msg.text():  # 对于群消息只处理@自己的
                print("tanming called in the room, reply generating...")
                text = re.sub(r'@.+?\s', "", msg.text())  # 去掉所有@和后面的昵称
                text = check.predict(text)[0]['target']
                await msg.room().say(soul(text, 0), [talker.contact_id])
        else:
            print("tanming called privately, reply generating...")
            text = check.predict(msg.text())[0]['target']
            await talker.say(soul(text, 1))
        return

    if talker.contact_id == users['kongmo']:
        # talker_dict['kongmo'] = talker
        if msg.room():
            if '@蔡晓' in msg.text():  # 对于群消息只处理@自己的
                print("kongmo called in the room, reply generating...")
                text = re.sub(r'@.+?\s', "", msg.text())  # 去掉所有@和后面的昵称
                text = check.predict(text)[0]['target']
                await msg.room().say(soul(text, 2), [talker.contact_id])
        else:
            print("kongmo called privately, reply generating...")
            text = check.predict(msg.text())[0]['target']
            await talker.say(soul(text, 3))
        return

    if talker.contact_id == users['lichao']:
        # talker_dict['lichao'] = talker
        if msg.room():
            if '@蔡晓' in msg.text():  # 对于群消息只处理@自己的
                print("lichao called in the room, reply generating...")
                text = re.sub(r'@.+?\s', "", msg.text())  # 去掉所有@和后面的昵称
                text = check.predict(text)[0]['target']
                await msg.room().say(soul(text, 4), [talker.contact_id])
        else:
            print("lichao called privately, reply generating...")
            text = check.predict(msg.text())[0]['target']
            await talker.say(soul(text, 5))
        return

    if talker.contact_id == users['sunruo']:
        # talker_dict['sunruo'] = talker
        if msg.room():
            if '@蔡晓' in msg.text():  # 对于群消息只处理@自己的
                print("sunruo called in the room, reply generating...")
                text = re.sub(r'@.+?\s', "", msg.text())  # 去掉所有@和后面的昵称
                text = check.predict(text)[0]['target']
                await msg.room().say(soul(text, 6), [talker.contact_id])
        else:
            print("sunruo called privately, reply generating...")
            text = check.predict(msg.text())[0]['target']
            await talker.say(soul(text, 7))
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
Authors:bigbrother666sh
On the basis of the following open source projects：
Yuan 1.0 Large pretrained LM - https://github.com/Shawn-Inspur/Yuan-1.0
Python Wechaty - https://github.com/wechaty/python-wechaty
PaddlePaddle - PaddlePaddle

editors: Qingling Li, Jingwei Hu, Jianing Zhao, Yang Ding
director:bigbrother666sh
       
2022 @ Copyright Projets Contributors
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
