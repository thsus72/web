from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password  # 비밀번호 해싱
from django.core.mail import send_mail
import random
from decouple import config

# 이메일 인증 코드를 저장하는 메모리 기반 스토리지
verification_code_storage = {}  # 이후 데이터베이스나 캐시로 대체 가능

# 로그인 뷰
def login_view(request):
    """
    사용자가 아이디와 비밀번호를 입력해 로그인하는 뷰.
    - 관리자 계정은 관리자 페이지(/admin/)로 리디렉션.
    - 일반 사용자는 메인 페이지로 리디렉션.
    """
    if request.method == 'POST':
        # 사용자 입력
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 사용자 인증
        user = authenticate(request, username=username, password=password)

        if user is not None:  # 인증 성공
            login(request, user)

            # 관리자 계정 처리
            if user.is_superuser:
                return redirect('/admin/')  # 관리자 페이지로 이동

            # 일반 사용자 처리
            return redirect('main')  # 메인 페이지로 이동
        else:
            # 인증 실패 시 오류 메시지
            messages.error(request, '아이디 또는 비밀번호가 일치하지 않습니다.')

    return render(request, 'accounts/login.html')  # 로그인 템플릿 렌더링

# 로그아웃 뷰
def logout_view(request):
    """
    사용자가 로그아웃하면 로그인 페이지로 리디렉션.
    """
    logout(request)
    return redirect('login')

# 메인 페이지 뷰
def main_page(request):
    """
    로그인 상태에 따라 다른 메인 페이지를 보여주는 뷰.
    - 로그인 상태: 사용자 이름을 포함한 메인 페이지.
    - 비로그인 상태: 방문자용 메인 페이지.
    """
    if request.user.is_authenticated:
        # 로그인한 사용자용 메인 페이지
        return render(request, 'accounts/main.html', {'username': request.user.username})
    # 비로그인 사용자용 메인 페이지
    return render(request, 'accounts/main_guest.html')

# 이메일 인증 코드 전송 함수
def send_verification_email(email):
    """
    사용자의 이메일로 인증 코드를 전송하는 함수.
    - 인증 코드는 랜덤 6자리 숫자로 생성.
    """
    # 랜덤 인증 코드 생성
    verification_code = str(random.randint(100000, 999999))

    # 이메일 발송
    send_mail(
        subject='회원가입 인증 코드',
        message=f'인증 코드는 {verification_code}입니다. 5분 내에 인증을 완료해주세요.',
        from_email=config('EMAIL_HOST_USER'),  # 발신자 이메일
        recipient_list=[email],  # 수신자 이메일
        fail_silently=False,
    )

    # 인증 코드를 저장
    verification_code_storage[email] = verification_code

# 회원가입 뷰
def signup_view(request):
    """
    회원가입을 처리하는 뷰.
    - 이메일 인증 코드 발송 및 검증 기능 포함.
    - 인증이 완료된 후 사용자 데이터를 데이터베이스에 저장.
    """
    email_sent = False  # 이메일 인증 여부 플래그
    if request.method == 'POST':
        action = request.POST.get('action')  # 버튼 동작 확인
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        email = request.POST.get('email')
        verification_code = request.POST.get('verification_code')

         # 이메일 인증 요청
        if action == 'send_code':
            # 비밀번호 확인 검증
            if password != password_confirm:
                messages.error(request, '비밀번호가 일치하지 않습니다.')
                return render(request, 'accounts/signup.html', {
                    'email_sent': False,
                    'username': username,
                    'password': password,
                    'password_confirm': password_confirm,
                    'email': email,
                })

            # 이메일 인증 코드 발송
            send_verification_email(email)
            email_sent = True
            messages.info(request, '입력하신 이메일로 인증 코드를 발송했습니다.')
            return render(request, 'accounts/signup.html', {
                'email_sent': email_sent,
                'username': username,
                'password': password,
                'password_confirm': password_confirm,
                'email': email,
            })

        # 회원가입 처리
        if action == 'signup':
            # 인증 코드 검증
            if email not in verification_code_storage or verification_code != verification_code_storage[email]:
                messages.error(request, '인증 코드가 올바르지 않습니다.')
                return render(request, 'accounts/signup.html', {
                    'email_sent': True,
                    'username': username,
                    'password': password,
                    'password_confirm': password_confirm,
                    'email': email,
                })

        # 데이터 저장 로직
        try:
            # 비밀번호 해싱 후 데이터베이스 저장
            hashed_password = make_password(password)
            User.objects.create(username=username, password=hashed_password, email=email)

            # 성공 메시지 및 인증 코드 삭제
            messages.success(request, '회원가입이 완료되었습니다. 로그인하세요.')
            del verification_code_storage[email]
            return redirect('login')  # 로그인 페이지로 리디렉션
        except IntegrityError:
            # 중복 데이터 오류 처리
            messages.error(request, '이미 존재하는 아이디 또는 이메일입니다.')

    return render(request, 'accounts/signup.html', {'email_sent': email_sent})  # 회원가입 템플릿 렌더링
