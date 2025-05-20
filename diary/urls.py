from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('kittiary.urls')),  # kittiary 앱의 모든 URL을 포함
] 