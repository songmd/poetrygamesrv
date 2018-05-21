# chat/urls.py
from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^$', views.index, name='index'),
    url(r'^login/$', views.user_login, name='user_login'),
    url(r'^user_info/$', views.update_user, name='update_user'),
    url(r'^share/$', views.add_share_info, name='add_share_info'),
    url(r'^rank/$', views.ranking, name='ranking'),
    url(r'^worldrank/$', views.world_ranking, name='world_ranking'),
    url(r'^history/$', views.history, name='history'),
    url(r'^poetry/$', views.get_poetry, name='get_poetry'),
    url(r'^collect/$', views.collect_poetry, name='collect_poetry'),
    url(r'^get_collect/$', views.get_collect, name='get_collect'),
    # url(r'^(?P<room_name>[^/]+)/$', views.room, name='room'),
]
