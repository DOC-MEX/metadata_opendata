from django.urls import path
from django.conf.urls.static import static
import os
from django.conf import settings
from . import views 

urlpatterns = [
    path('', views.form_opendata, name='form_opendata'),
    path('review/', views.review_metadata, name='review_metadata'),
    path('submit/', views.submit_metadata, name='submit_metadata'),
    path('view_json/<str:filename>/', views.view_json, name='view_json'),
    path('serve_json/<str:filename>/', views.serve_json_file, name='serve_json_file'),
] 
