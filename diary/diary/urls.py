"""
URL configuration for diary project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from kittiary import views
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="회상 다이어리 API",
        default_version='v1',
        description="""회상 다이어리 API 문서입니다.
        
일기 작성, 조회, 수정, 삭제 등의 기능을 제공합니다.

## 주요 기능
- 일기 CRUD
- 월별 일기 조회
- 가족 관계 관리
- 통계 조회
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('', views.index, name="index"),
    path('home/', views.home, name="home"),
    path('profile/', views.ProfileView.as_view(), name="profile"),
    path('api/v1/', include('kittiary.urls')),
    path('api/oauth/login', views.kakao_login, name='kakao_login'),
    path('login', views.login_error, name='login_error'),
    path("api/v1/auth/", include("dj_rest_auth.urls")),   # /login /logout /refresh
    path("api/v1/auth/registration/", include("dj_rest_auth.registration.urls")),
    
    # Swagger UI
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    from django.views.generic import TemplateView
    urlpatterns += [
        path('', TemplateView.as_view(template_name='index.html')),
        path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
        path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    ]
