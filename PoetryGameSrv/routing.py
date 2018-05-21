# from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
import rhesis_contest.routing

# from rhesis_contest.consumers import MockContestConsumer

# application = ProtocolTypeRouter({
#
#     'websocket': AuthMiddlewareStack(
#         URLRouter(
#             rhesis_contest.routing.websocket_urlpatterns
#         )
#     ),
# })

application = ProtocolTypeRouter({
    'websocket': URLRouter(
        rhesis_contest.routing.websocket_urlpatterns
    ),
    # 'channel': ChannelNameRouter({
    #     "mock-contest": MockContestConsumer,
    # }),

})
