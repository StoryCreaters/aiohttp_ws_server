"""
路由处理，信号广播
"""
import aiohttp
from aiohttp import web
import asyncio
import CPlayer

dic = dict()
get_dict = False


class Dispatcher:
    async def login(players, myplayer, name):
        """
        :param players: player lists 
        :param myplayer: Player player
        :param name:    name to login
        """
        print('get: ', name)
        login = True
        send = bytes()
        for player in players:
            if player.get_name() == name:
                login = False
                break
        if login:
            myplayer.set_name(name)
            send = b'login'
        else:
            send = b'already exist'
        # print(type(send))
        await myplayer.send_msg(send)

    async def room_select(rooms, myplayer):
        """
        :param rooms: room lists
        :param myplayer:  CURPLAYER
        :return: message
        """
        l = list()
        for i in range(4):
            if rooms[i].in_game():
                l.append('5')
            else:
                l.append(str(rooms[i].player_nums()))
        s = ' '.join(l)
        await myplayer.send_msg(bytes(s.encode('ascii')))

    async def get_in_room(myplayer, rooms, index):
        """
        :param myplayer:  myplayer
        :param rooms:  list of rooms
        """
        if rooms[index].join_able():
            rooms[index].add_player(myplayer)
            await myplayer.send_msg(b'joined')

    async def select_player(myplayer, requests, msg):
        """
        :param requests:请求
        :param msg:     str 的LIST,第一个参数表示类型('Chat', 'Select') 
        """
        type = msg[0]
        if type == 'Chat':
            msg = [bytes(s.encode('ascii')) for s in msg]
            send = b' '.join(msg[1:])
            print('myname :', myplayer)
            await broadcast(b'chat ' + bytes(str(myplayer).encode('ascii')) + b' ' + send, ws_lists=requests.app['Players'])
        elif type == 'Start':
            myplayer.select = msg[1]
            # 暂时不能取消准备
            myplayer.ready = True
            if myplayer.ready:
                room = myplayer.cur_room()
                if room.check_start():
                    await room.start_game()
        # why not here
        elif type == 'roomselect':
            myplayer.exit_room()

    async def in_game_logic(myplayer, requests, msg):
        # myplayer 死亡

        if msg[0] == 'DIE':
            print('die here~')
            await myplayer.chara_die()
            return
        elif msg[0] == 'state':
                if msg[1] == myplayer.get_last_state():
                    msg[1] = '6'
                else:
                    myplayer.set_last_state(msg[1])
        # 插入本人名
        if msg[0] == 'use' or msg[0] == 'state':
            msg.insert(1, str(myplayer))
        msg = (s.encode('ascii') for s in msg)
        b_message = b' '.join(map(bytes, msg))
        await broadcast_except_me(myplayer, requests.app['Players'], b_message)


async def broadcast(msg, ws_lists):
    """
    :param msg: message string
    :param ws_lists: ws lists
    """
    for web_link in ws_lists:
        await web_link.send_msg(msg)

async def broadcast_except_me(myplayer, players, msg):
    room = myplayer.cur_room()
    for player in room.players:
        if player == myplayer:
            # print('same...')
            continue
        # print(b'send ' + msg, player)
        await player.send_msg(msg)

async def message_dispatcher(msg, request, myplayer):
    """
    :param msg: a string
    :param ws_lists: the lists of player
    :return:  dispatch the work for the program
    """
    datas = str(msg).split(' ')
    msg_type = datas[0]
    if msg_type == 'login':
        await Dispatcher.login(request.app['Players'], myplayer, datas[1])
    elif msg_type == 'roomselect':
        # 进入界面
        if datas[1] == 'in':
            myplayer.state = CPlayer.Datatype.ROOMSELECT
            # send the state of the room
            await Dispatcher.room_select(request.app['Rooms'], myplayer)
        elif datas[1] == 'roomselect':
            await myplayer.exit_room()
            myplayer.state = CPlayer.Datatype.ROOMSELECT
            for cur_player in request.app['Players']:
                if cur_player.state == CPlayer.Datatype.ROOMSELECT:
                    await Dispatcher.room_select(request.app['Rooms'], cur_player)
        elif datas[1] == 'tostart':
            myplayer.set_name('')
            myplayer.state = CPlayer.Datatype.LOGIN
        else:
            await Dispatcher.get_in_room(myplayer, request.app['Rooms'], int(datas[1]))
            for cur_player in request.app['Players']:
                if cur_player.state == CPlayer.Datatype.ROOMSELECT:
                    if cur_player == myplayer:
                        pass
                        # await myplayer.send_msg(b'joined')
                    await Dispatcher.room_select(request.app['Rooms'], cur_player)
    elif msg_type == 'playerselect':
        await Dispatcher.select_player(myplayer, request, datas[1:])
    elif msg_type == 'ongame':
        await Dispatcher.in_game_logic(myplayer, request, datas[1:])

async def sleep_and_broadcast(ws_lists):
    while True:
        await asyncio.sleep(59)
        broadcast(b'a minute passed', ws_lists)


async def handler(requests):
    global get_dict
    ws = web.WebSocketResponse()
    if not get_dict:
        global dic
        dic = requests.app
        get_dict = True
    print('a user connected')
    await ws.prepare(requests)
    # add player into it
    cur_player = CPlayer.Player(ws)
    requests.app['Players'].append(cur_player)
    try:
        async for msg in ws:
            # print('recv {}'.format(msg.data))
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == b'close':
                    break
                await message_dispatcher(msg.data, requests, cur_player)
    finally:
        await cur_player.purge()
        requests.app['Players'].remove(cur_player)
    print(cur_player, 'log out')
    return ws

