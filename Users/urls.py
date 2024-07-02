from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns=[
    path('Registration/',views.Registration,name='Reg'),
    path('', views.Registration,name='Reg'),
    path('register/user/', views.UserRegistration, name='user_registration'), 
]