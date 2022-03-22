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

director = 'wxid_a6xxa7n11u5j22'
with open('users.json') as f:
    users = json.load(f)

rooms = []

# 读取example语料
data=[]
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

names=["谭明","孔墨","李超","孙若"]
#记忆机制
memory={"tm":[],"km":[],"lc":[],"sr":[]}
#群聊中触发AI活跃的关键词
activity=["@蔡晓","大家说","蔡晓你","大家怎么","咱们说","咱们怎么","蔡晓啥","蔡晓怎么"]

def soul(text, a,b):
    who=names[a]
    lines=data[a]
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
    # print(results)
    yuan.add_example(
        Example(inp=who+"说：“"+results[0]['text_1']+"”", out=lines[lines.index(results[0]['text_1'] + '\n') + 1].strip('\n')))
    if results[1]['similarity'] > 0.5:
        yuan.add_example(
            Example(inp=who+"说：“"+results[1]['text_1']+"”", out=lines[lines.index(results[1]['text_1'] + '\n') + 1].strip('\n')))
    if results[2]['similarity'] > 0.5:
        yuan.add_example(
            Example(inp=who+"说：“"+results[2]['text_1']+"”", out=lines[lines.index(results[2]['text_1'] + '\n') + 1].strip('\n')))
    time.sleep(1)
    reply = yuan.submit_API(''.join(memory[b]), trun="”")
    with open(who+".txt", 'a', encoding='utf-8') as f:
      f.write(who+":"+text+"---top-3 similarity："+str(results[0]['similarity'])+"，"+str(results[1]['similarity'])+"，"+str(results[2]['similarity'])+"\n")
      f.write(reply+"\n")
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
        #talker_dict['tm'] = talker
        print("tanming has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return
    if msg.text() == '这是孔墨':
        users['kongmo'] = talker.contact_id
        #talker_dict['km'] = talker
        print("kongmo has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return
    if msg.text() == '这是李超':
        users['lichao'] = talker.contact_id
        #talker_dict['lc'] = talker
        print("lichao has registed, the latest users list is:", users)
        await talker.say('这是蔡晓')
        return
    if msg.text() == '这是孙若':
        users['sunruo'] = talker.contact_id
        #talker_dict['sr'] = talker
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
        #代码1，存储当场用户，在本场所有玩家注册后，必须执行这一步，期间有必要程序关闭或重启就不会丢失用户信息
        if text == '1':
            with open('users.json', 'w') as f:
                json.dump(users, f)
            print("users dict has been saved as bigbro/users.jason")

        # 代码2开头，导演接入，实现主动发信息（todo群消息mention）—— 暂时直接用程序挂载的Windows客户端直接操作，效果是一样的
        #if text=="欢迎各位，我是本场游戏导演，下面我来宣布游戏规则，请各位务必遵守":  #欢迎语注册房间
            #talker_dict["rm"]=msg.room()
        #if text[0]=='2':
            #tosay=talker_dict[text[1:3]]
            #if tosay:
                #await tosay.say(text[3:])
            #else:
                #print(text[1:3]+"has not registed yet. can not send by director")

        #代码2 记忆遗忘机制，当出现重复回复的时候使用，无法区分群聊，rm会遗忘所有群聊记忆
        if text[0] == '2':
            if text[1:3] == 'tm':
                memory['tm'] = []
            if text[1:3] == 'km':
                memory['km'] = []
            if text[1:3] == 'lc':
                memory['lc'] = []
            if text[1:3] == 'sr':
                memory['sr'] = []
            if text[1:3] == 'rm':
                rooms = []
            print(text[1:3]+"'s memory has been forgiven")
        return

    if talker.contact_id == users['tanming']:
        # talker_dict['tanming'] = talker
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id]=[]
            #if len(re.sub(r'\s', "",re.sub(r'@.+?\s', "", msg.text())))==0:
            text = re.sub(r'\s', "，",msg.text())
            text = text.replace("@", "").replace("#", "")
            if len(memory[msg.room().room_id]) > 5:
                memory[msg.room().room_id].pop(0)
            memory[msg.room().room_id].append("谭明说：“"+text+"”")
            print(memory[msg.room().room_id])
            for key in activity:
                if key in msg.text():
                    print("tanming called in the room, reply generating...")
                    reply=soul(text, 0, msg.room().room_id)
                    await msg.room().say(reply)
                    return
        else:
            print("tanming called privately, reply generating...")
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("#", "，")
            if len(memory["tm"]) > 3:
                memory["tm"].pop(0)
            memory["tm"].append("谭明说：“"+text+"”")
            reply = soul(text, 0, "tm")
            await talker.say(reply)
            print(memory["tm"])
        return

    if talker.contact_id == users['kongmo']:
        # talker_dict['kongmo'] = talker
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id]=[]
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("@", "").replace("#", "")
            if len(memory[msg.room().room_id]) > 5:
                memory[msg.room().room_id].pop(0)
            memory[msg.room().room_id].append("孔墨说：“"+text+"”")
            print(memory[msg.room().room_id])
            for key in activity:
                if key in msg.text():
                    print("kongmo called in the room, reply generating...")
                    reply=soul(text, 1, msg.room().room_id)
                    await msg.room().say(reply)
                    return
        else:
            print("kongmo called privately, reply generating...")
            text = re.sub(r'\s', "，",msg.text())
            text = text.replace("#", "，")
            if len(memory["km"]) > 3:
                memory["km"].pop(0)
            memory["km"].append("孔墨说：“"+text+"”")
            reply = soul(text, 1, "km")
            await talker.say(reply)
            print(memory["km"])
        return

    if talker.contact_id == users['lichao']:
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id]=[]
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("@", "").replace("#", "")
            if len(memory[msg.room().room_id]) > 5:
                memory[msg.room().room_id].pop(0)
            memory[msg.room().room_id].append("李超说：“"+text+"”")
            print(memory[msg.room().room_id])
            for key in activity:
                if key in msg.text():
                    print("lichao called in the room, reply generating...")
                    reply=soul(text, 2, msg.room().room_id)
                    await msg.room().say(reply)
                    return
        else:
            print("lichao called privately, reply generating...")
            text = re.sub(r'\s', "，",msg.text())
            text = text.replace("#", "，")
            if len(memory["lc"]) > 3:
                memory["lc"].pop(0)
            memory["lc"].append("李超说：“"+text+"”")
            reply = soul(text, 2, "lc")
            await talker.say(reply)
            print(memory["lc"])
        return

    if talker.contact_id == users['sunruo']:
        # talker_dict['sunruo'] = talker
        if msg.room():
            if msg.room().room_id not in rooms:
                rooms.append(msg.room().room_id)
                memory[msg.room().room_id]=[]
            text = re.sub(r'\s', "，", msg.text())
            text = text.replace("@", "").replace("#", "")
            if len(memory[msg.room().room_id]) > 5:
                memory[msg.room().room_id].pop(0)
            memory[msg.room().room_id].append("孙若说：“"+text+"”")
            print(memory[msg.room().room_id])
            for key in activity:
                if key in msg.text():
                    print("sunruo called in the room, reply generating...")
                    reply=soul(text, 3, msg.room().room_id)
                    await msg.room().say(reply)
                    return
        else:
            print("sunruo called privately, reply generating...")
            text = re.sub(r'\s', "，",msg.text())
            text = text.replace("#", "，")
            if len(memory["sr"]) > 3:
                memory["sr"].pop(0)
            memory["sr"].append("孙若说：“"+text+"”")
            reply = soul(text, 3, "sr")
            await talker.say(reply)
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
