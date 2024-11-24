from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'), # 메인 페이지
    path('login/', views.login_view, name='login'), # 로그인 페이지
]