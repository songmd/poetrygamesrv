from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'openid', 'nick_name', 'coin', 'level', 'level_score', 'win', 'fail', 'avatar_url']

    ordering = ['-openid']

    search_fields = ['nick_name', 'avatar_url']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # search_fields = ['chengyu']
    pass


@admin.register(UserShareInfo)
class UserShareInfoAdmin(admin.ModelAdmin):
    pass


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    pass


@admin.register(GameRoom)
class GameRoomAdmin(admin.ModelAdmin):
    pass


@admin.register(Poetry)
class PoetryAdmin(admin.ModelAdmin):
    pass


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'question']
    pass
