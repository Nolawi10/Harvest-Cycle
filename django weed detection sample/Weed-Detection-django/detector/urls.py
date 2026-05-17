# detector/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('start_stream/<str:source_type>/', views.start_stream, name='start_stream'),
    path('stop_stream/', views.stop_stream, name='stop_stream'),
    path('upload_video/', views.upload_video, name='upload_video'),
]
