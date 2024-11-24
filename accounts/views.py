from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password  # 비밀번호 해싱

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 관리자일 경우 관리자 페이지로 리디렉션
            if user.is_superuser:
                return redirect('/admin/')  # 관리자 페이지 URL

            # 일반 사용자일 경우 메인 페이지로 리디렉션
            return redirect('main')
        else:
            messages.error(request, '아이디 또는 비밀번호가 일치하지 않습니다.') # 오류 메시지

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def main_page(request):
    if request.user.is_authenticated:
        return render(request, 'accounts/main.html', {'username': request.user.username})
    return render(request, 'accounts/main_guest.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        # 데이터 저장 로직
        try:
            hashed_password = make_password(password)  # 비밀번호 해싱
            User.objects.create(username=username, password=hashed_password, email=email)
            messages.success(request, '회원가입이 완료되었습니다. 로그인하세요.')
            return redirect('login')
        except IntegrityError:
            messages.error(request, '이미 존재하는 아이디 또는 이메일입니다.')

    return render(request, 'accounts/signup.html')