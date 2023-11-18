from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path('ws/', consumers.SensorConsumer.as_asgi()),
    re_path('ws2/', consumers.MicConsumer.as_asgi()),
    re_path('ws3/', consumers.Mic2Consumer.as_asgi()),
    re_path('ws4/', consumers.Mic3Consumer.as_asgi()),
]