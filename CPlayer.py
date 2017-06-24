from enum import Enum, unique

@unique
class Datatype(Enum):
    LOGIN      = 'login'
    ROOMSELECT = 'selectroom'
    CHAT       = 'chat'
    START      = 'startgame'
    IN         = 'ingame'
    DIE        = 'die'


class Player:
    def __init__(self, ws):
        """
        :param ws: connection 
        """
        # 连接的
        self.conn = ws
        # 房间连接
        self._room = None
        self._name = None
        # 选择的人物序号
        self.select = 1
        # 人物之前的状态
        self.last_state = '5'
        self.alive = True
        # 是否准备
        self.ready = False
        self.state = Datatype.LOGIN

    def get_last_state(self):
        return self.last_state

    async def chara_die(self):
        """
        :return: 人物死亡 
        """
        self.alive = False
        if self._room is not None:
            await self.cur_room().check_game_state()

    def set_last_state(self, val):
        self.last_state = val

    async def exit_room(self):
        self._room.remove_player(self)
        await self._room.check_game_state()
        self._room = None

    def get_in_room(self, room):
        self._room = room

    def cur_room(self):
        return self._room

    def set_name(self, in_name):
        """
        :param in_name: set the player name into the name we want 
        """
        self._name = in_name

    def get_name(self):
        return self._name

    async def send_msg(self, msg):
        """
        :param msg:  send byte message
        """
        # print('send: ' + str(msg))
        await self.conn.send_bytes(msg)

    def __str__(self):
        return self.get_name()

    async def purge(self):
        """
        remove the player 
        """
        await self.chara_die()
        if self._room is not None:
            await self.exit_room()

    def game_over(self):
        self.alive = True
        # 是否准备
        self.ready = False
        self.state = Datatype.CHAT
