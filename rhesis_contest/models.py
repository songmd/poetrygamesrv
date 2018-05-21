import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
import random
from django.db import transaction
from django.db.models import Q

level_list = [0, 2, 8, 21, 48, 75, 108, 141, 192, 243]


class Question(models.Model):
    stem = models.CharField(_('题干'), max_length=128)
    dynasty = models.CharField(_('朝代'), max_length=16)
    author = models.CharField(_('作者'), max_length=16)
    title = models.CharField(_('标题'), max_length=128)
    type = models.IntegerField(_('上句或下句'), default=1)

    option1 = models.CharField(_('选项1'), max_length=128)
    option2 = models.CharField(_('选项2'), max_length=128)
    option3 = models.CharField(_('选项3'), max_length=128)
    option4 = models.CharField(_('选项4'), max_length=128)

    answer = models.IntegerField(_('答案'), default=0)

    tags = models.CharField(_('标签'), max_length=256, null=True)

    reference = models.ForeignKey('Poetry', on_delete=models.SET_NULL, null=True, verbose_name=_('出处'))

    popularity = models.IntegerField(_('流行度'), default=1)

    class Meta:
        verbose_name = _('问题')
        verbose_name_plural = _('问题')

    def __str__(self):
        return self.stem

    def to_json(self):
        return dict(id=self.id,
                    stem=str(self.stem),
                    dynasty=str(self.dynasty),
                    author=str(self.author),
                    title=str(self.title),
                    type=int(self.type),
                    option1=str(self.option1),
                    option2=str(self.option2),
                    option3=str(self.option3),
                    option4=str(self.option4),
                    answer=int(self.answer),
                    tags=str(self.tags))

    def get_profile(self):
        answer = str(getattr(self, 'option%d' % (self.answer + 1)))
        text = [str(self.stem), answer] if self.type == 1 else [answer, str(self.stem)]
        return dict(ref_id=self.reference_id, text=text, author=self.author, title=self.title)


def uuid_char():
    return uuid.uuid4().hex


class Xiaoxue(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)


class Chuzhong(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)


class Gaozhong(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)


class Tangshi(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)


class Songcijingxuan(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)


class Poetry(models.Model):
    dynasty = models.CharField(_('朝代'), max_length=16)
    author = models.CharField(_('作者'), max_length=16)
    title = models.CharField(_('标题'), max_length=128)
    annotation = models.TextField(_('注释'))
    full_text = models.TextField(_('全文'))
    translation = models.TextField(_('翻译'))

    class Meta:
        verbose_name = _('诗词')
        verbose_name_plural = _('诗词')

    def __str__(self):
        return '%s(%s.%s)' % (self.title, self.dynasty, self.author)

    def to_json(self):
        return dict(dynasty=self.dynasty, author=self.author, title=self.title, annotation=self.annotation,
                    full_text=self.full_text, tran=self.translation)


class History(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)

    def __str__(self):
        return '%s___%s' % (self.user.nick_name, self.question.title)

    class Meta:
        verbose_name = _('历史')
        verbose_name_plural = _('历史')


class Collect(models.Model):
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE)
    poetry = models.ForeignKey('Poetry', on_delete=models.CASCADE)

    def __str__(self):
        return '%s___%s' % (self.user.nick_name, self.poetry.title)

    class Meta:
        verbose_name = _('收藏')
        verbose_name_plural = _('收藏')
        unique_together = ('user', 'poetry',)


class AppUser(models.Model):
    id = models.CharField(_('用户标识'), primary_key=True, max_length=128, default=uuid_char)
    openid = models.CharField(_('微信OpenId'), max_length=128, null=True, blank=True)
    session_key = models.CharField(_('会话密钥'), max_length=128, null=True, blank=True)
    unionid = models.CharField(_('统一Id'), max_length=128, null=True, blank=True)
    # user_info = models.TextField(_('用户信息'), max_length=512, null=True)
    coin = models.IntegerField(_('金币'), default=1000)

    nick_name = models.CharField(_('昵称'), max_length=256, null=True, blank=True)
    avatar_url = models.CharField(_('头像'), max_length=256, null=True, blank=True)

    is_mock = models.BooleanField(_('是否虚拟用户'), default=False)

    random_order = models.IntegerField(_('随机顺序'), default=0)

    level = models.IntegerField(_('级别'), default=1)

    win = models.IntegerField(_('胜局'), default=0)

    fail = models.IntegerField(_('败局'), default=0)

    level_score = models.IntegerField(_('当前级别分数'), default=0)

    # questions = models.ManyToManyField('Question', related_name=_('已测验问题'), editable=False)

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')

    def __str__(self):
        return self.openid

    def get_star(self):
        # level_list = [0, 2, 8, 21, 48, 75, 108, 141, 192, 243]
        return min(9, int(self.level_score / int(level_list[self.level] / self.level)))

    def user_info(self):
        return dict(nick_name=str(self.nick_name) if self.nick_name is not None else '',
                    avatar_url=str(self.avatar_url) if self.avatar_url is not None else '',
                    level=int(self.level),
                    coin=int(self.coin),
                    win=int(self.win),
                    fail=int(self.fail),
                    star=self.get_star(),
                    is_mock=bool(self.is_mock),
                    mock_answer=self.player.answer_info() if self.is_mock and hasattr(self, 'player') else '')

    def update_user(self, nick_name, avatar_url, coin, score):
        if nick_name is not None:
            self.nick_name = nick_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if coin is not None:
            self.coin += coin
        if score is not None:
            self.win += 1 if score > 0 else 0
            self.fail += 1 if score < 0 else 0
        if score:
            self.level_score += score
            if self.level_score < 0:
                self.level_score = 0
            if self.level_score >= level_list[self.level] and self.level < 9:
                self.level += 1
                self.level_score = 0

        if nick_name or avatar_url or coin or score:
            self.save()

    def add_question_id(self, questions):
        if self.is_mock:
            return
        with transaction.atomic():
            for q_id in questions:
                h = History.objects.create(user=self, question_id=q_id)
                h.save()


class Player(models.Model):
    user = models.OneToOneField('AppUser', related_name='player', on_delete=models.CASCADE, verbose_name=_('用户'))

    # 用于给websocket 发送消息
    channel_name = models.CharField(_('通道名'), max_length=128)

    answer1 = models.IntegerField(_('答案1'), null=True)
    time1 = models.IntegerField(_('答题1时间'), null=True)

    answer2 = models.IntegerField(_('答案2'), null=True)
    time2 = models.IntegerField(_('答题2时间'), null=True)

    answer3 = models.IntegerField(_('答案3'), null=True)
    time3 = models.IntegerField(_('答题3时间'), null=True)

    answer4 = models.IntegerField(_('答案4'), null=True)
    time4 = models.IntegerField(_('答题4时间'), null=True)

    answer5 = models.IntegerField(_('答案5'), null=True)
    time5 = models.IntegerField(_('答题5时间'), null=True)

    class Meta:
        verbose_name = _('玩家')
        verbose_name_plural = _('玩家')

    # 随机生成答案
    def mock_answer(self, level, answers):
        self.answer1, self.answer2, self.answer3, self.answer4, self.answer5 = answers
        if random.randint(1, 25) + level < 13:
            self.answer1 = random.randint(0, 3)
        if random.randint(1, 25) + level < 13:
            self.answer2 = random.randint(0, 3)
        if random.randint(1, 25) + level < 13:
            self.answer3 = random.randint(0, 3)
        if random.randint(1, 25) + level < 13:
            self.answer4 = random.randint(0, 3)
        if random.randint(1, 25) + level < 13:
            self.answer5 = random.randint(0, 3)

        self.time1 = self.random_time()  # random.randint(0, 6) + random.randint(1, 7) + random.randint(0, 6)
        self.time2 = self.random_time()  # random.randint(0, 6) + random.randint(1, 7) + random.randint(0, 6)
        self.time3 = self.random_time()  # random.randint(0, 6) + random.randint(1, 7) + random.randint(0, 6)
        self.time4 = self.random_time()  # random.randint(0, 6) + random.randint(1, 7) + random.randint(0, 6)
        self.time5 = self.random_time()  # random.randint(0, 6) + random.randint(1, 7) + random.randint(0, 6)

    def random_time(self):
        if random.randint(1, 3) != 1:
            return random.randint(1, 7)
        else:
            return random.randint(1, 14)

    def __str__(self):
        return '%s__%s' % (self.user.id, self.user.openid)

    def set_default(self, channel_name):
        self.channel_name = channel_name
        self.answer1 = None
        self.time1 = None
        self.answer2 = None
        self.time2 = None
        self.answer3 = None
        self.time3 = None
        self.answer4 = None
        self.time4 = None
        self.answer5 = None
        self.time5 = None

    def answer_info(self):
        return dict(an1=self.answer1, an2=self.answer2, an3=self.answer3, an4=self.answer4, an5=self.answer5,
                    t1=self.time1, t2=self.time2, t3=self.time3, t4=self.time4, t5=self.time5)


class GameRoom(models.Model):
    player1 = models.ForeignKey('Player', related_name='p1_room', on_delete=models.CASCADE, null=True,
                                verbose_name=_('游戏房间'))
    player2 = models.ForeignKey('Player', related_name='p2_room', on_delete=models.CASCADE, null=True,
                                verbose_name=_('游戏房间'))
    question1 = models.ForeignKey('Question', related_name='q1_room', on_delete=models.SET_NULL, null=True,
                                  verbose_name=_('问题1'))

    question2 = models.ForeignKey('Question', related_name='q2_room', on_delete=models.SET_NULL, null=True,
                                  verbose_name=_('问题2'))

    question3 = models.ForeignKey('Question', related_name='q3_room', on_delete=models.SET_NULL, null=True,
                                  verbose_name=_('问题3'))

    question4 = models.ForeignKey('Question', related_name='q4_room', on_delete=models.SET_NULL, null=True,
                                  verbose_name=_('问题4'))

    question5 = models.ForeignKey('Question', related_name='q5_room', on_delete=models.SET_NULL, null=True,
                                  verbose_name=_('问题5'))

    for_friend = models.BooleanField(_('只为好友'), default=False)

    level = models.IntegerField(_('级别'), default=1)

    #   房间类型 0 为排位，1 为学生
    type = models.IntegerField(_('类型'), default=0)

    # 0 为初始状态，1为一人同意，2为全部同意开始
    continue_play = models.IntegerField(_('是否继续游戏'), default=0)

    class Meta:
        verbose_name = _('游戏房间')
        verbose_name_plural = _('游戏房间')

    def __str__(self):
        return '%s vs %s' % (self.player1, self.player2)

    # [66, 16,8, 4, 2,1,1,1,1]
    # (1,67)(67,83)(83,91)(91,95)(95,97)(97,98)(98,99)(99,100),(100,101)
    # 76% 11% %3 % 2 %2 %1 %1 %1 %1
    def get_random_level(self, level):
        r_int = random.randint(1, 100)
        r_rang = 1
        if r_int <= 76:
            r_rang = 1
        elif r_int <= 87:
            r_rang = 2
        elif r_int <= 92:
            r_rang = 3
        elif r_int <= 95:
            r_rang = 4
        elif r_int <= 96:
            r_rang = 5
        elif r_int <= 97:
            r_rang = 6
        elif r_int <= 98:
            r_rang = 7
        elif r_int <= 99:
            r_rang = 8
        else:
            r_rang = 9
        lv_table = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [2, 3, 1, 4, 5, 6, 7, 8, 9],
            [3, 4, 2, 5, 1, 6, 7, 8, 9],
            [4, 5, 3, 1, 6, 2, 7, 8, 9],
            [5, 6, 4, 3, 7, 2, 8, 9, 1],
            [6, 7, 5, 8, 4, 9, 3, 2, 1],
            [7, 8, 6, 9, 5, 4, 3, 2, 1],
            [8, 9, 7, 6, 5, 4, 3, 2, 1],
            [9, 8, 7, 6, 5, 4, 3, 2, 1],
        ]
        return lv_table[level - 1][r_rang - 1]

    def select_questions(self):
        first_id = Question.objects.first().id
        last_id = Question.objects.last().id

        # level1 = self.player1.user.level if self.player1 is not None else 1
        # level2 = self.player2.user.level if self.player2 is not None else 1
        # level = max(level1, level2)
        if self.type == 1:
            self.question1_id = random.choice(id_dict[self.level])
            self.question2_id = random.choice(id_dict[self.level])
            self.question3_id = random.choice(id_dict[self.level])
            self.question4_id = random.choice(id_dict[self.level])
            self.question5_id = random.choice(id_dict[self.level])
        else:
            self.question1_id = self.random_question(self.level, first_id, last_id)
            self.question2_id = self.random_question(self.level, first_id, last_id)
            self.question3_id = self.random_question(self.level, first_id, last_id)
            self.question4_id = self.random_question(self.level, first_id, last_id)
            self.question5_id = self.random_question(self.level, first_id, last_id)

    def random_question(self, level, first_id, last_id):

        tran_level = self.get_random_level(level)
        print('tran_level', tran_level)
        if tran_level == 1:
            return random.choice(id_dict[1])
        elif tran_level == 2:
            return random.choice(id_dict[2])
        elif tran_level == 3:
            return random.choice(id_dict[3])
        elif tran_level == 4:
            return random.randint(first_id, min(first_id + 1000, last_id))
        elif tran_level == 5:
            return random.randint(first_id, min(first_id + 2000, last_id))
        elif tran_level == 6:
            return random.randint(first_id, min(first_id + 3000, last_id))
        elif tran_level == 7:
            return random.randint(first_id, min(first_id + 5000, last_id))
        elif tran_level == 8:
            return random.randint(first_id, min(first_id + 8000, last_id))
        else:
            return random.randint(first_id, last_id)

    # def random_question(self, level, first_id, last_id):
    #
    #     # 1级 19/24  9级 1/8
    #     if random.randint(0, 23) + level * 2 < 21:
    #         return random.randint(first_id, 200)
    #     # 1级 6/10  9级 2/10
    #     elif random.randint(1, 10) * 2 + level < 14:
    #         return random.randint(200, 600)
    #     # 1级 5/10 9级 1/10
    #     elif random.randint(1, 10) * 2 + level < 13:
    #         return random.randint(600, 950)
    #     else:
    #         return random.randint(600, last_id)

    def get_questions(self):
        return [self.question1.to_json(), self.question2.to_json(), self.question3.to_json(), self.question4.to_json(),
                self.question5.to_json()]

    def get_questions_id(self):
        return self.question1_id, self.question2_id, self.question3_id, self.question4_id, self.question5_id


class UserShareInfo(models.Model):
    from_user = models.ForeignKey('AppUser', related_name='share_info', on_delete=models.CASCADE, verbose_name=_('分享者'))
    to_user = models.ForeignKey('AppUser', related_name='shared_info', on_delete=models.CASCADE, verbose_name=_('分享至'))

    class Meta:
        verbose_name = _('用户分享')
        verbose_name_plural = _('用户分享')
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return '{0}({1})-->{2}({3})'.format(self.from_user.openid, self.from_user.nick_name, self.to_user.openid,
                                            self.to_user.nick_name)


# def import_questions():
#     import sqlite3
#     from django.db import transaction
#
#     conn = sqlite3.connect('questions(2).db')
#     cursor = conn.cursor()
#     cursor.execute(
#         'SELECT question,dynasty,type,answer,option1,option2,option3,option4,author,title,tag FROM questions')
#     with  transaction.atomic():
#         for question, dynasty, type, answer, option1, option2, option3, option4, author, title, tag in cursor:
#             new_q = Question.objects.create(stem=question.strip(),
#                                             type=type,
#                                             dynasty=dynasty.strip(),
#                                             answer=answer,
#                                             option1=option1.strip(),
#                                             option2=option2.strip(),
#                                             option3=option3.strip(),
#                                             option4=option4.strip(),
#                                             author=author.strip(),
#                                             title=title.strip(),
#                                             tags=tag.strip())
#             # for t in tags:
#             #     to = RhesisTag.objects.get_or_create(tag=t)
#             #     # to.save()
#             #     new_q.tags.add(t)
#             new_q.save()
#         # print(question)

#
# def import_mock_user():
#     import os
#     import random
#     from django.db import transaction
#
#     files = [f for f in os.listdir('wxtx') if not os.path.isdir(f)]
#     names = []
#     with open('name2.txt') as nf:
#         while True:
#             name = nf.readline()
#             if name:
#                 names.append(name.strip())
#             else:
#                 break
#
#     random.shuffle(names)
#     random.shuffle(files)
#
#     with  transaction.atomic():
#         for i in range(min(len(files), len(names))):
#             user = AppUser.objects.create(openid='',
#                                           session_key='',
#                                           nick_name=names[i],
#                                           avatar_url=files[i],
#                                           is_mock=True)
#             user.save()


def import_mock_user_ex():
    import os
    import random
    from django.db import transaction

    files = [f for f in os.listdir('wxtx') if not os.path.isdir(f)]
    names = []
    with open('name2.txt') as nf:
        while True:
            name = nf.readline()
            if name:
                names.append(name.strip())
            else:
                break

    random.shuffle(names)
    random.shuffle(files)

    def get_level(index):
        # 300,300,300
        # 200
        # 200
        # 150
        # 150
        # 100
        # 60
        if index <= 300:
            l = 1
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 600:
            l = 2
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 900:
            l = 3
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 1150:
            l = 4
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 1400:
            l = 5
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 1600:
            l = 6
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 1800:
            l = 7
            return l, random.randint(0, level_list[l] - 1)
        elif index <= 2000:
            l = 8
            return l, random.randint(0, level_list[l] - 1)
        else:
            l = 9
            return l, random.randint(0, level_list[l] - 1)

    with  transaction.atomic():
        index = 0
        for i in range(min(len(files), len(names))):
            index += 1
            level, score = get_level(index)
            user = AppUser.objects.create(openid='',
                                          session_key='',
                                          nick_name=names[i],
                                          avatar_url=files[i],
                                          is_mock=True,
                                          level=level,
                                          level_score=score,
                                          coin=random.randint(5, 1500) * 10)
            user.save()


def import_poetry():
    import sqlite3
    import re
    from django.db import transaction

    conn = sqlite3.connect('sanyu_poetry.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id,dynasty,author,title,annotation,full_text,translation FROM poetry')

    rf1 = re.compile('（.+）')

    rf2 = re.compile('\(.+\)')

    rt = re.compile('/.+')

    with  transaction.atomic():
        for id, dynasty, author, title, annotation, full_text, translation in cursor:
            tt = rt.sub('', title.strip())
            f_t = rf1.sub('', full_text.strip())
            f_t = rf2.sub('', f_t)
            new_poetry = Poetry.objects.create(id=id,
                                               dynasty=dynasty.strip(),
                                               author=author.strip(),
                                               title=tt,
                                               annotation=annotation.strip(),
                                               full_text=f_t,
                                               translation=translation.strip())
            new_poetry.save()


def import_q():
    import sqlite3
    import re
    from django.db import transaction

    conn = sqlite3.connect('sanyu_poetry.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT stem,dynasty,type,answer,option1,option2,option3,option4,author,title,tags,popularity,reference_id FROM question')
    rt = re.compile('/.+')
    with  transaction.atomic():
        for stem, dynasty, type, answer, option1, option2, option3, option4, author, title, tags, popularity, reference_id in cursor:
            tt = rt.sub('', title.strip())
            new_q = Question.objects.create(stem=stem.strip(),
                                            type=type,
                                            dynasty=dynasty.strip(),
                                            answer=answer,
                                            option1=option1.strip(),
                                            option2=option2.strip(),
                                            option3=option3.strip(),
                                            option4=option4.strip(),
                                            author=author.strip(),
                                            title=tt,
                                            tags=tags.strip(),
                                            popularity=popularity,
                                            reference_id=reference_id)
            new_q.save()


def create_level_table():
    xiaoxue = Question.objects.filter(Q(tags__contains='小学') | Q(tags__contains='早教'))
    chuzhong = Question.objects.filter(tags__contains='初中')
    gaozhong = Question.objects.filter(tags__contains='高中')
    tangshi = Question.objects.filter(tags__contains='唐诗')
    songcijingxuan = Question.objects.filter(tags__contains='宋词精选')
    with  transaction.atomic():
        for item in xiaoxue:
            obj = Xiaoxue.objects.create(question=item)
            obj.save()
        for item in chuzhong:
            obj = Chuzhong.objects.create(question=item)
            obj.save()
        for item in gaozhong:
            obj = Gaozhong.objects.create(question=item)
            obj.save()
        for item in tangshi:
            obj = Tangshi.objects.create(question=item)
            obj.save()
        for item in songcijingxuan:
            obj = Songcijingxuan.objects.create(question=item)
            obj.save()
    print(Xiaoxue.objects.count(), Chuzhong.objects.count(), Gaozhong.objects.count(), Tangshi.objects.count(),
          Songcijingxuan.objects.count())


def load_id():
    print('load id')
    ret = {
        1: [item.question_id for item in Xiaoxue.objects.all()],
        2: [item.question_id for item in Chuzhong.objects.all()],
        3: [item.question_id for item in Gaozhong.objects.all()],
        4: [item.question_id for item in Tangshi.objects.all()],
        5: [item.question_id for item in Songcijingxuan.objects.all()],
    }

    return ret


id_dict = load_id()
