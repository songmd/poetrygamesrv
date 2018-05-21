# from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import *
from django.db.models import Q
from django.db import transaction
import threading
import random
from asgiref.sync import async_to_sync


class RhesisContestConsumer(AsyncJsonWebsocketConsumer):
    # 此consumer所代表的玩家信息
    _player_info = dict()

    # 对手玩家信息
    _rival_player_info = dict()

    # 用于给对手consumer发送消息
    _rival_channel_name = None

    # 游戏房间id
    _room_id = None

    #  玩家用户id
    _user_token = None

    #  对手玩家用户id
    _rival_user_token = None

    #   问题集
    _questions = None

    #   是否已断开
    _is_disconnect = False

    #   是否收到断开通知事件
    _is_notified_disconnect = False

    def check_or_mock(self):
        with transaction.atomic():
            room = GameRoom.objects.select_for_update().filter(pk=self._room_id).first()
            if room is None:
                return
            if room.player1 is None or room.player2 is not None:
                return
            mock_user = AppUser.objects.select_for_update().filter(is_mock=True, player=None,
                                                                   level=room.player1.user.level).order_by(
                'random_order').first()
            if mock_user is None:
                print('error')
                return
            mock_user.random_order = random.randint(1, 10000)
            mock_player = Player.objects.create(user=mock_user, channel_name='mock-contest')
            mock_player.mock_answer(room.level, (int(room.question1.answer),
                                                 int(room.question2.answer),
                                                 int(room.question3.answer),
                                                 int(room.question4.answer),
                                                 int(room.question5.answer)))

            room.player2 = mock_player

            room.save()
            mock_player.save()
            mock_user.save()
        async_to_sync(self.channel_layer.send)(self.channel_name,
                                               dict(type='start.event',
                                                    channel_name=None,
                                                    user_token=mock_player.user.id,
                                                    play_info=mock_player.user.user_info(),
                                                    room_id=self._room_id))

    async def connect(self):
        print('connect')
        await self.accept()

    async def disconnect(self, code):
        #   取消定时器
        print('disconnect')
        if self.start_timer is not None:
            self.start_timer.cancel()

    async def receive_json(self, content, **kwargs):
        print(content, self.channel_name)
        # print(self.channel_name)

        #   开始或者加入游戏
        if content['type'] == 'start_or_join':

            print('start game', content['user'])
            success = await self.db_start_or_join_game(content['user'], int(content.get('level', 1)))
            if not success:
                await  self.send_json(dict(err_code=-1, type='error'), close=True)
            if self._rival_channel_name is not None:
                # 事件通知对手consumer 游戏开始
                await self.send_start_event()
                # 给客户端发送游戏开始信息
                await self.send_start_response()
            else:
                self.start_timer = threading.Timer(random.uniform(2, 6), self.check_or_mock)
                self.start_timer.start()

        #   继续游戏
        if content['type'] == 'continue':

            print('continue game')
            success, start_game = await self.db_continue_game()
            if not success:
                await  self.send_json(dict(err_code=-1, type='error'), close=True)
            if self._rival_channel_name is not None and success and start_game:
                # 事件通知对手consumer 游戏开始
                await self.send_start_event()
                # 给客户端发送游戏开始信息
                await self.send_start_response()
            elif success and start_game:
                # 给客户端发送游戏开始信息
                await self.send_start_response()

        # 开始游戏等待好友加入
        if content['type'] == 'start':
            success = await self.db_start_game(content['user'])
            if not success:
                await  self.send_json(dict(err_code=-1, type='error'), close=True)

        # 进入好友的游戏
        if content['type'] == 'join':
            success = await self.db_join_game(content['user'], content.get('friend'))
            if not success:
                await  self.send_json(dict(err_code=-1, type='error'), close=True)

            if self._rival_channel_name is not None:
                # 事件通知对手consumer 游戏开始
                await self.send_start_event()
                # 给客户端发送游戏开始信息
                await self.send_start_response()

        # 报告答案
        if content['type'] == 'report':
            success, turn_result = await self.db_report_answer(content.get('turn'),
                                                               content.get('answer'),
                                                               content.get('time_elapsed'))

            if not success:
                await  self.send_json(dict(err_code=-1, type='error'), close=True)
            if turn_result is not None:
                await self.send_report_event(turn_result)
                await self.send_report_response(turn_result)

    #   发送给对手consumer游戏开始的通知
    async def send_start_event(self):
        print('send start event')
        await self.channel_layer.send(self._rival_channel_name,
                                      dict(type='start.event',
                                           channel_name=self.channel_name,
                                           user_token=self._user_token,
                                           play_info=self._player_info,
                                           room_id=self._room_id))

    #   发送给对手consumer，本consumer客户端退出通知
    async def send_disconnect_event(self):
        # 对手是模拟的，无需通知
        if self._rival_channel_name is None:
            return
        await self.channel_layer.send(self._rival_channel_name,
                                      dict(type='disconnect.event'))

    #   发送给对手consumer回合报告的通知
    async def send_report_event(self, turn_result):
        # 对手是模拟的，无需通知
        if self._rival_channel_name is None:
            return
        await self.channel_layer.send(self._rival_channel_name,
                                      dict(type='report.event',
                                           channel_name=self.channel_name,
                                           user_token=self._user_token,
                                           room_id=self._room_id,
                                           turn_result=turn_result))

    #   响应对手consumer的断开游戏通知
    async def disconnect_event(self, event):
        print('disconnect_event', event)
        self._is_notified_disconnect = True
        if not self._is_disconnect:
            await self.send_json(
                dict(type='rival_disconnect', err_code=0))

    #   响应对手consumer的开始游戏通知
    async def start_event(self, event):
        print('start_event', event)
        self._rival_channel_name = event['channel_name']
        self._rival_user_token = event['user_token']
        self._rival_player_info = event['play_info']
        await self.send_start_response()

    async def disconnect(self, close_code):
        # Called when the socket closes
        self._is_disconnect = True
        if not self._is_notified_disconnect:
            await self.send_disconnect_event()
        await self.db_close_game()
        print('disconnect:', close_code)

    #   发送开始游戏的应答
    async def send_start_response(self):
        resp = dict(type='start_resp', err_code=0, questions=self._questions, user_info=self._player_info,
                    rival_user_info=self._rival_player_info)
        print('send_start_respone:', resp)
        await self.send_json(resp)

    #   发送游戏回合报告的应答
    async def send_report_response(self, turn_result):
        print('report_resp:', turn_result)
        await self.send_json(
            dict(type='report_resp', err_code=0, result=turn_result))

    #   响应对手consumer的报告通知
    async def report_event(self, event):
        print('report_event', event)

        rival_result = event['turn_result']

        # 发给本consumer客户端的回合结果数据与发给对手consumer的数据相反
        turn_result = dict(turn=rival_result['turn'],
                           answer=rival_result['rival_answer'],
                           time_elapsed=rival_result['rival_time_elapsed'],
                           rival_answer=rival_result['answer'],
                           rival_time_elapsed=rival_result['time_elapsed'])

        await self.send_report_response(turn_result)

    #   报告答案
    @database_sync_to_async
    def db_report_answer(self, turn, answer, time_elapsed):

        # 如果是第二个报告，返回本回合结果
        turn_result = None

        if turn is None or answer is None or time_elapsed is None or turn > 5 or turn < 1:
            return False, turn_result
        with transaction.atomic():
            room = GameRoom.objects.select_for_update().filter(pk=self._room_id).first()
            if room is None or room.player1 is None or room.player2 is None:
                return False, turn_result

            player = room.player1 if room.player1.user.id == self._user_token else room.player2
            rival_player = room.player1 if room.player1.user.id == self._rival_user_token else room.player2

            answer_attr_name = 'answer%d' % turn
            time_attr_name = 'time%d' % turn
            setattr(player, answer_attr_name, answer)
            setattr(player, time_attr_name, time_elapsed)
            player.save()

        #   获取对手本回合答题信息
        rival_answer = getattr(rival_player, answer_attr_name, None)
        rival_time_elapsed = getattr(rival_player, time_attr_name, None)

        if rival_answer is not None and rival_time_elapsed is not None:
            turn_result = dict(turn=turn,
                               answer=answer,
                               time_elapsed=time_elapsed,
                               rival_answer=rival_answer,
                               rival_time_elapsed=rival_time_elapsed)

        return True, turn_result

    #   开始游戏的初始化工作
    def _start_init(self):
        # 此consumer所代表的玩家信息
        self._player_info = dict(nick_name='', avatar_url='')

        # 对手玩家信息
        self._rival_player_info = dict(nick_name='', avatar_url='')

        # 用于给对手consumer发送消息
        self._rival_channel_name = None

        # 游戏房间id
        self._room_id = None

        #  玩家用户id
        self._user_token = None

        #  对手玩家用户id
        self._rival_user_token = None

        #   问题集
        self._questions = None

        #   是否已断开
        self._is_disconnect = False

        #   是否收到断开通知事件
        self._is_notified_disconnect = False

    #   开始或者加入游戏
    @database_sync_to_async
    def db_start_or_join_game(self, user, level):

        self._start_init()

        self._user_token = user
        with transaction.atomic():
            print('start_user:', user)
            player, created = Player.objects.update_or_create(user_id=user)
            player.set_default(self.channel_name)

            self._player_info = player.user.user_info()

            room = GameRoom.objects.select_for_update().filter(Q(player1=None) | Q(player2=None), for_friend=False,
                                                               level=level).first()
            if room is None:
                room = GameRoom.objects.create(level=level)
                room.select_questions()
            else:
                rival_player = room.player1 if room.player1 is not None else room.player2
                self._rival_channel_name = rival_player.channel_name
                self._rival_user_token = rival_player.user.id
                self._rival_player_info = rival_player.user.user_info()

            if room.player1 is None:
                room.player1 = player
            elif room.player2 is None:
                room.player2 = player

            player.user.add_question_id(room.get_questions_id())
            room.save()
            player.save()

            self._questions = room.get_questions()
            self._room_id = room.id
        return True

    #   在原有房间继续继续游戏
    @database_sync_to_async
    def db_continue_game(self):

        start_game = False
        with transaction.atomic():
            room = GameRoom.objects.select_for_update().filter(pk=self._room_id).first()
            if room is None or room.player1 is None or room.player2 is None:
                return False, start_game

            if room.player2.user.is_mock:
                start_game = True
                room.select_questions()
            elif room.continue_play == 1:
                start_game = True
                room.continue_play = 0
            else:
                room.continue_play = 1
                room.select_questions()

            room.player1.set_default(room.player1.channel_name)
            room.player2.set_default(room.player2.channel_name)

            if room.player2.user.is_mock:
                room.player2.mock_answer(room.level, (int(room.question1.answer),
                                                      int(room.question2.answer),
                                                      int(room.question3.answer),
                                                      int(room.question4.answer),
                                                      int(room.question5.answer)))
                # 更新模拟用户信息，主要是模拟答案
                self._rival_player_info = room.player2.user.user_info()

            room.player1.user.add_question_id(room.get_questions_id())
            room.player2.user.add_question_id(room.get_questions_id())
            room.save()
            room.player1.save()
            room.player2.save()

        self._questions = room.get_questions()

        return True, start_game

    # 开始游戏等待好友加入
    @database_sync_to_async
    def db_start_game(self, user):

        self._start_init()

        self._user_token = user
        with transaction.atomic():
            player, created = Player.objects.update_or_create(user_id=user)
            player.set_default(self.channel_name)

            self._player_info = player.user.user_info()

            room = GameRoom.objects.create(for_friend=True, level=player.user.level)
            room.select_questions()
            room.player1 = player
            player.user.add_question_id(room.get_questions_id())
            room.save()
            player.save()

        self._questions = room.get_questions()
        self._room_id = room.id

        return True

    # 进入好友的游戏
    @database_sync_to_async
    def db_join_game(self, user, friend):

        if friend is None:
            print('error: friend is none')
            return False

        self._start_init()

        self._user_token = user
        with transaction.atomic():
            player, created = Player.objects.update_or_create(user_id=user)
            player.set_default(self.channel_name)

            self._player_info = player.user.user_info()

            room = GameRoom.objects.select_for_update().filter(player1__user__id=friend, player2=None).first()
            if room is None:
                return False

            room.player2 = player
            self._rival_channel_name = room.player1.channel_name
            self._rival_user_token = room.player1.user.id
            self._rival_player_info = room.player1.user.user_info()

            player.user.add_question_id(room.get_questions_id())
            player.save()
            room.save()

        self._questions = room.get_questions()
        self._room_id = room.id
        return True

    #   结束游戏,清除数据库
    @database_sync_to_async
    def db_close_game(self):
        print('enter close')
        with transaction.atomic():
            room = GameRoom.objects.select_for_update().filter(pk=self._room_id).first()
            if room is not None:
                print('db close game')
                if room.player1 is not None:
                    room.player1.delete()
                if room.player2 is not None:
                    room.player2.delete()
                room.delete()
