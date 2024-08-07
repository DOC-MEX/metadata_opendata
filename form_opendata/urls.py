from django.urls import path
from . import views 

urlpatterns = [
    path('', views.form_opendata, name='form_opendata'),
    path('review/', views.review_metadata, name='review_metadata'),
    path('submit/', views.submit_metadata, name='submit_metadata'),
]
