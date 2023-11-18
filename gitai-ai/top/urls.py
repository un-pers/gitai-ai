from django.urls import path
from . import views
from django.conf.urls.static import static
from gitai_ai import settings

urlpatterns = [
    path('', views.top, name='top'),
    path('voice', views.voice, name='voice'),
    path('voice2', views.voice2, name='voice2'),
    path('result', views.result, name='result'),
    path('result2', views.result2, name='result2'),
    path('graph', views.graph, name='graph'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)