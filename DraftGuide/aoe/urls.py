from django.urls import path

from . import views

urlpatterns = [
    path('submit/', views.submit, name='form_submit'),
    path('<slug:tourny_name>/', views.index, name='tourny'),
    path('', views.index, name='index'),
]
