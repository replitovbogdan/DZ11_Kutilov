from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('clean/', views.clean_uploads, name='clean_uploads'),  # опционально: для очистки
]