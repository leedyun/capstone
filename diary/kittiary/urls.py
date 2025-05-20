from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, FamilyViewSet, DiaryViewSet, QnAViewSet, StatsViewSet
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

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # User endpoints
    path('api/v1/users/me/', user_me, name='user-me'),
    path('api/v1/users/profile/', user_profile, name='user-profile'),
    
    # API endpoints
    path('', include(router.urls)),
    path('oauth/login', views.kakao_login, name='kakao_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Auth endpoints
    path('auth/refresh/', refresh_token, name='token-refresh'),
    path('auth/logout/', logout, name='logout'),
    
    # Nested QnA routes
    path('diaries/<int:diary_id>/qna/', QnAViewSet.as_view({'get': 'list', 'post': 'create'}), name='qna-list'),
    path('qna/<int:pk>/', QnAViewSet.as_view({
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='qna-detail'),
] 