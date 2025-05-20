from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, FamilyViewSet, DiaryViewSet, QnAViewSet, StatsViewSet, ProfileView
from .auth_views import refresh_token, logout

# UserViewSet의 추가 액션에 대한 URL 패턴
user_profile = UserViewSet.as_view({
    'get': 'profile_options',
    'put': 'profile'
})

user_me = UserViewSet.as_view({
    'get': 'me'
})

# Router 설정
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'families', FamilyViewSet, basename='family')
router.register(r'diaries', DiaryViewSet, basename='diary')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'qnas', QnAViewSet, basename='qna')

# 템플릿 뷰 URL 패턴
template_urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('profile/', ProfileView.as_view(), name='profile'),
]

# API URL 패턴
api_urlpatterns = [
    # User endpoints
    path('users/me/', user_me, name='user-me'),
    path('users/profile/', user_profile, name='user-profile'),
    
    # API endpoints
    path('', include(router.urls)),
    
    # OAuth endpoints
    path('oauth/login/', views.kakao_login, name='kakao-login'),
    path('oauth/callback/', views.kakao_callback, name='kakao-callback'),
    path('oauth/logout/', views.logout_view, name='logout'),
    
    # Auth endpoints
    path('auth/refresh/', refresh_token, name='token-refresh'),
    path('auth/logout/', logout, name='logout'),
]

# URL 패턴 결합
urlpatterns = template_urlpatterns + api_urlpatterns

# HTTPS로 변경
redirect_uri = 'https://localhost:8001/api/oauth/callback/' 