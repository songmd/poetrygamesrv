from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.db import transaction

# Create your views here.
from django.utils.safestring import mark_safe
import json

#
# def index(request):
#     return render(request, 'index.html', {})
#
#
# def room(request, room_name):
#     return render(request, 'room.html', {
#         'room_name_json': mark_safe(json.dumps(room_name))
#     })


WX_APP_ID = 'wxfb2683ac6ce7db4e'
WX_APP_SECRET = '77e0c611a5612c886575ab92c11c8b60'


class RetCode(object):
    SUCCESS = '0000'
    INVALID_PARA = '0001'
    USER_NOT_EXIST = '0002'
    SHOP_NOT_EXIST = '0003'
    WXSRV_ERROR = '0004'
    SRV_EXCEPTION = '0005'


def get_openid(js_code):
    appid, secret = WX_APP_ID, WX_APP_SECRET
    url = "https://api.weixin.qq.com/sns/jscode2session"
    args = {
        'appid': appid,
        'secret': secret,
        'js_code': js_code,
        'grant_type': 'authorization_code',
    }
    sess = requests.Session()
    resp = sess.get(url, params=args)

    return json.loads(resp.content.decode("utf-8"))


def user_login(request):
    resp = {}
    js_code = request.GET.get('js_code', None)
    user_token = request.GET.get('user_token', None)

    try:
        # 有js_code 则user_token不生效
        if js_code is not None:
            wx_data = get_openid(js_code)
            if 'errcode' in wx_data:
                resp['retcode'] = RetCode.WXSRV_ERROR
                return JsonResponse(resp)
            try:
                app_user = AppUser.objects.get(openid=wx_data['openid'])

            except AppUser.DoesNotExist:
                app_user = AppUser.objects.create()
                app_user.openid = wx_data['openid']

            app_user.session_key = wx_data['session_key']
            if 'unionid' in wx_data:
                app_user.unionid = wx_data['unionid']

            app_user.save()
            resp['user_token'] = app_user.id
            resp['user_info'] = app_user.user_info()

            resp['retcode'] = RetCode.SUCCESS
            return JsonResponse(resp)
        if user_token is not None:
            try:
                app_user = AppUser.objects.get(pk=user_token)
            except AppUser.DoesNotExist:
                resp['retcode'] = RetCode.USER_NOT_EXIST
                return JsonResponse(resp)
            resp['retcode'] = RetCode.SUCCESS

            resp['user_token'] = app_user.id
            resp['user_info'] = app_user.user_info()

            return JsonResponse(resp)
    except BaseException as e:
        print(e)
        resp['retcode'] = RetCode.SRV_EXCEPTION
        return JsonResponse(resp)

    resp['retcode'] = RetCode.INVALID_PARA
    return JsonResponse(resp)


@csrf_exempt
def update_user(request):
    resp = {}
    post_data = json.loads(request.body)
    user_token = post_data.get('user_token', None)
    nick_name = post_data.get('nick_name', None)
    avatar_url = post_data.get('avatar_url', None)
    coin = post_data.get('coin', None)
    score = post_data.get('score', None)

    # print(user_token, nick_name, avatar_url, coin, score)
    if not user_token:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)
    try:
        app_user = AppUser.objects.get(pk=user_token)
    except AppUser.DoesNotExist:
        resp['retcode'] = RetCode.USER_NOT_EXIST
        return JsonResponse(resp)

    app_user.update_user(nick_name, avatar_url, coin, score)

    resp['user_info'] = app_user.user_info()

    resp['retcode'] = RetCode.SUCCESS
    # print(resp)
    return JsonResponse(resp)


@csrf_exempt
def add_share_info(request):
    resp = {}
    post_data = json.loads(request.body)
    user_token = post_data.get('user_token', None)
    from_user_token = post_data.get('from_user', None)

    if not user_token or not from_user_token or user_token == from_user_token:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)
    try:
        app_user = AppUser.objects.get(pk=user_token)
        from_user = AppUser.objects.get(pk=from_user_token)
    except AppUser.DoesNotExist:
        resp['retcode'] = RetCode.USER_NOT_EXIST
        return JsonResponse(resp)

    share_info, created = UserShareInfo.objects.get_or_create(from_user_id=from_user_token, to_user_id=user_token)
    if created:
        with transaction.atomic():
            from_user.coin += from_user.level * 3 * 50
            share_info.save()
            from_user.save()

    resp['retcode'] = RetCode.SUCCESS

    return JsonResponse(resp)


def world_ranking(request):
    resp = {}
    result = AppUser.objects.all().order_by('-level', '-level_score')[:100]

    resp['retcode'] = RetCode.SUCCESS

    resp['rank'] = []
    for row in result:
        resp['rank'].append(row.user_info())
    # print(resp)
    return JsonResponse(resp)


def ranking(request):
    resp = {}
    user_token = request.GET.get('user_token', None)

    if not user_token:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)
    try:
        app_user = AppUser.objects.get(pk=user_token)
    except AppUser.DoesNotExist:
        resp['retcode'] = RetCode.USER_NOT_EXIST
        return JsonResponse(resp)

    result = AppUser.objects.filter(
        Q(share_info__to_user=user_token) | Q(shared_info__from_user=user_token) | Q(pk=user_token)).order_by(
        '-level', '-level_score')

    # distinct('id')

    resp['retcode'] = RetCode.SUCCESS
    resp['rank'] = []

    users = set()
    for row in result:
        if row.id not in users:
            users.add(row.id)
            resp['rank'].append(row.user_info())
        if len(users) == 100:
            break
    # print(resp)
    return JsonResponse(resp)


def history(request):
    resp = {}
    user_token = request.GET.get('user_token', None)
    off_set = int(request.GET.get('off_set', 0))

    if not user_token:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)
    try:
        app_user = AppUser.objects.get(pk=user_token)
    except AppUser.DoesNotExist:
        resp['retcode'] = RetCode.USER_NOT_EXIST
        return JsonResponse(resp)
    # s = slice(-25, None) if off_set == 0 else slice(-off_set - 25, -off_set)
    # result = app_user.questions[s]

    result = History.objects.filter(user_id=user_token)

    resp['retcode'] = RetCode.SUCCESS
    resp['history'] = []
    poetries = set()
    index = 0
    count = 0
    for row in reversed(result):
        if row.question.reference.id not in poetries:
            poetries.add(row.question.reference.id)
            if index >= off_set:
                resp['history'].append(row.question.get_profile())
                count += 1
                if count == 50:
                    break
            index += 1

    # print(resp)
    return JsonResponse(resp)


# URL  poetry/
# 参数  user_token  id(诗词id)
# 功能  获取单首诗词信息   传user_token  将额外返回此诗词收藏信息，不传功能如旧
def get_poetry(request):
    resp = {}
    id = int(request.GET.get('id', None))

    user_token = request.GET.get('user_token', None)

    collect = 1
    if not id:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)
    try:
        poetry = Poetry.objects.get(pk=id)
    except Poetry.DoesNotExist:
        resp['retcode'] = RetCode.USER_NOT_EXIST
        return JsonResponse(resp)
    if user_token:
        try:
            collect_obj = Collect.objects.get(user_id=user_token, poetry_id=id)
        except Collect.DoesNotExist:
            collect = 0
    else:
        collect = 0

    resp['retcode'] = RetCode.SUCCESS
    resp['poetry'] = poetry.to_json()
    resp['collect'] = collect

    return JsonResponse(resp)


# url collect/
# 参数：  user_token    id(诗词id）  dis_collect（是否取消诗词， 缺省为收藏，其它非零值为取消收藏
# 功能：  收藏或者取消收藏
@csrf_exempt
def collect_poetry(request):
    resp = {}
    post_data = json.loads(request.body)
    user_token = post_data.get('user_token', None)
    id = int(post_data.get('id', None))
    dis_collect = int(post_data.get('dis_collect', None))

    if not user_token or not id:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)

    collect, created = Collect.objects.get_or_create(user_id=user_token, poetry_id=id)
    if created and not dis_collect:
        collect.save()
    elif dis_collect and not created:
        collect.delete()

    resp['retcode'] = RetCode.SUCCESS

    return JsonResponse(resp)


# url get_collect/
# 参数：  user_token    off_set
# 功能：  获取收藏诗词，一次50条


# def get_collect(request):
#     resp = {}
#     user_token = request.GET.get('user_token', None)
#     off_set = int(request.GET.get('off_set', 0))
#
#     if not user_token:
#         resp['retcode'] = RetCode.INVALID_PARA
#         return JsonResponse(resp)
#
#     result = Collect.objects.filter(user_id=user_token)
#
#     resp['retcode'] = RetCode.SUCCESS
#     resp['collect'] = []
#     index = 0
#     count = 0
#     for row in reversed(result):
#         if index >= off_set:
#             resp['collect'].append(row.poetry_id)
#             count += 1
#             if count == 50:
#                 break
#         index += 1
#
#     # print(resp)
#     return JsonResponse(resp)

def get_collect(request):
    resp = {}
    user_token = request.GET.get('user_token', None)
    off_set = int(request.GET.get('off_set', 0))

    if not user_token:
        resp['retcode'] = RetCode.INVALID_PARA
        return JsonResponse(resp)
    try:
        app_user = AppUser.objects.get(pk=user_token)
    except AppUser.DoesNotExist:
        resp['retcode'] = RetCode.USER_NOT_EXIST
        return JsonResponse(resp)
    # s = slice(-25, None) if off_set == 0 else slice(-off_set - 25, -off_set)
    # result = app_user.questions[s]
    collects = [row.poetry_id for row in Collect.objects.filter(user_id=user_token)]
    result = History.objects.filter(user_id=user_token, question__reference_id__in=collects)

    resp['retcode'] = RetCode.SUCCESS
    resp['collect'] = []
    poetries = set()
    index = 0
    count = 0
    for row in reversed(result):
        if row.question.reference.id not in poetries:
            poetries.add(row.question.reference.id)
            if index >= off_set:
                resp['collect'].append(row.question.get_profile())
                count += 1
                if count == 50:
                    break
            index += 1

    # print(resp)
    return JsonResponse(resp)
