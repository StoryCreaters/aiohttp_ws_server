import CPlayer
import handler
import random

class Room:
    def __init__(self, index):
        """
        :param index: interger of the code of the room 
        """
        # store the player of the games
        self.players = list()
        # is the game on playing
        self.start = False

    def player_nums(self):
        """
        :return:number of players 
        """
        return len(self.players)

    def play(self):
        # 开始游戏
        self.start = True

    def in_game(self):
        return self.start

    # 可加入
    def join_able(self):
        if self.player_nums() == 4 or self.in_game():
            return False
        return True

    def add_player(self, player):
        """
        :param player: a player to insert in 
        """
        self.players.append(player)
        player.get_in_room(self)
        player.state = CPlayer.Datatype.CHAT

    def remove_player(self, player):
        """
        :param player: the player to removed  
        """
        self.players.remove(player)

    def check_start(self):
        # to do: change it back to <= 1
        if self.player_nums() <= 1:
            return False
        start = True
        for player in self.players:
            if not player.ready:
                start = False
                break
        return start

    async def start_game(self):
        """
        :return: start room game 
        """
        self.start = True
        l = list()
        for i, player in enumerate(self.players):
            player.ready = False
            s_tmp = bytes(player.get_name().encode('ascii')) + b' ' + bytes(str(i + 1).encode('ascii')) + b' ' + \
                    bytes(str(player.select).encode('ascii'))
            l.append(s_tmp)

        # TODO:考虑加入随机的种子
        send = b'start ' + bytes(str(random.randint(0, 32767)).encode('ascii')) + b' ' + bytes(str(self.player_nums()).encode('ascii')) + b' ' + b' '.join(l)
        for player in self.players:
            await player.send_msg(send)

    async def check_game_state(self):
        if not self.in_game():
            print('not in game')
            return
        else:
            live = list()
            self.start = False
            for player in self.players:
                if player.alive:
                    live.append(player)
            if len(live) > 1:
                return
            # win
            for player in self.players:
                if player in live:
                    await player.send_msg(b'win')
                else:
                    await player.send_msg(b'lose')
                player.game_over()
            # todo: broadcast rooms
            for dic_p in handler.dic['Players']:
                await handler.Dispatcher.room_select(handler.dic['Rooms'], dic_p)
