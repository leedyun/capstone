from django.shortcuts import render, redirect
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from datetime import datetime, date, timedelta
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth, TruncWeek
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, get_user_model
from django.conf import settings
import requests
import json
from .models import User, Family, Diary, QnA, Stats
from .serializers import (
    UserSerializer, UserProfileSerializer, FamilySerializer, DiarySerializer,
    DiaryDetailSerializer, QnASerializer, StatsSerializer, StatsSummarySerializer,
    StatsCategorySerializer
)
import uuid
from .exceptions import AuthErrorCode, AuthException
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.renderers import JSONRenderer
from django.http import JsonResponse, HttpResponseRedirect
import logging
from django.contrib.auth import authenticate
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import login as auth_login
from django.views import View
import jwt

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    return render(request,'index.html')

def home(request):
    return render(request,'home.html')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def kakao_login(request):
    client_id = '6242b32743c06796acdfd168cd435126'
    redirect_uri = 'https://localhost:8000/api/oauth/callback/'
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    )

@api_view(['GET'])
@permission_classes([AllowAny])
def kakao_callback(request):
    try:
        code = request.GET.get("code")
        if not code:
            return JsonResponse({"error": "No code provided"}, status=400)

        client_id = '6242b32743c06796acdfd168cd435126'
        redirect_uri = 'https://localhost:8000/api/oauth/callback/'
        
        # 카카오 토큰 받기
        token_request = requests.get(
            f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={client_id}&redirect_uri={redirect_uri}&code={code}"
        )
        token_json = token_request.json()
        error = token_json.get("error", None)
        if error is not None:
            return JsonResponse({"error": "INVALID_CODE"}, status=400)
        
        access_token = token_json.get("access_token")
        
        # 카카오 사용자 정보 받기
        profile_request = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_json = profile_request.json()
        
        kakao_account = profile_json.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        nickname = profile.get("nickname", "User")
        
        # 카카오 ID를 사용하여 사용자 식별
        kakao_id = str(profile_json.get("id"))
        
        try:
            # 카카오 ID로 사용자 찾기
            user = User.objects.get(social_login_id=kakao_id)
        except User.DoesNotExist:
            # 새 사용자 생성
            user = User.objects.create(
                username=f"kakao_{kakao_id}",
                name=nickname,
                social_login_id=kakao_id
            )
            user.set_unusable_password()
            user.save()
        
        # JWT 토큰 생성
        token = jwt.encode(
            {'user_id': user.id},
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        # 프론트엔드로 리다이렉트하면서 토큰을 URL 파라미터로 전달
        frontend_url = 'https://localhost:5174/home'
        return redirect(f"{frontend_url}?token={token}")
        
    except Exception as e:
        logger.error(f"Kakao callback error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception:
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['get'])
    def me(self, request):
        """현재 로그인한 사용자의 정보를 반환합니다."""
        try:
            user = self.get_object()
            serializer = self.get_serializer(user)
            data = serializer.data
            # 프로필 완성 여부 추가
            data['is_new_user'] = not user.is_profile_completed
            return Response(data)
        except Exception as e:
            logger.error(f"Error in me endpoint: {str(e)}")
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['get', 'put'])
    def profile(self, request):
        """사용자 프로필을 조회하거나 업데이트합니다."""
        if request.method == 'GET':
            return self.profile_options(request)
        
        user = self.get_object()
        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 필수 필드가 모두 채워졌는지 확인
            if user.name and user.birth_date and user.gender:
                user.is_profile_completed = True
                user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def profile_options(self, request):
        """프로필 옵션(성별, 가족관계 등)을 반환합니다."""
        return Response({
            'relationships': dict(Family.RELATIONSHIP_CHOICES),
            'genders': dict(User.GENDER_CHOICES)
        })

class FamilyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FamilySerializer

    def get_queryset(self):
        return Family.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DiaryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DiarySerializer

    def get_queryset(self):
        queryset = Diary.objects.filter(user=self.request.user)
        
        # 월별 필터링
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        if year and month:
            queryset = queryset.filter(diary_date__year=year, diary_date__month=month)
        
        return queryset.order_by('diary_date')

    def perform_create(self, serializer):
        diary = serializer.save(user=self.request.user)
        
        # 회상일기인 경우 QnA 데이터 생성
        if diary.category == 'REMINISCENCE':
            try:
                qna_data = json.loads(diary.content)
                qnas_to_create = []
                for item in qna_data:
                    qnas_to_create.append(QnA(
                        diary=diary,
                        question=item['question'],
                        correct_answer=item['answer'],
                        user_response=item['response']
                    ))
                QnA.objects.bulk_create(qnas_to_create)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in diary content: {diary.content}")
            except KeyError as e:
                logger.error(f"Missing required key in QnA data: {e}")

    def perform_update(self, serializer):
        diary = serializer.instance
        
        # 회상일기인 경우 QnA 데이터 업데이트
        if diary.category == 'REMINISCENCE':
            try:
                qna_data = json.loads(serializer.validated_data['content'])
                
                # 기존 QnA 삭제
                diary.qnas.all().delete()
                
                # 새로운 QnA 생성
                qnas_to_create = []
                for item in qna_data:
                    qnas_to_create.append(QnA(
                        diary=diary,
                        question=item['question'],
                        correct_answer=item['answer'],
                        user_response=item['response']
                    ))
                QnA.objects.bulk_create(qnas_to_create)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in diary content: {serializer.validated_data['content']}")
            except KeyError as e:
                logger.error(f"Missing required key in QnA data: {e}")
        
        super().perform_update(serializer)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.category == 'REMINISCENCE':
            try:
                # QnA 데이터를 JSON 형식으로 변환
                qna_data = []
                for qna in instance.qnas.all():
                    qna_data.append({
                        'question': qna.question,
                        'answer': qna.correct_answer,
                        'response': qna.user_response
                    })
                instance.content = json.dumps(qna_data)
            except Exception as e:
                logger.error(f"Error processing QnA data: {e}")
        
        serializer = DiaryDetailSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """월별 일기 목록을 반환합니다."""
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not year or not month:
            return Response(
                {"error": "year와 month 파라미터가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        diaries = self.get_queryset().filter(
            diary_date__year=year,
            diary_date__month=month
        ).values('id', 'diary_date', 'category')
        
        # 날짜별로 일기 데이터 구성
        calendar_data = {}
        for diary in diaries:
            date_str = diary['diary_date'].strftime('%Y-%m-%d')
            diary_data = {
                'id': diary['id'],
                'diary_date': date_str,
                'category': diary['category']
            }
            
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            calendar_data[date_str].append(diary_data)
            
        return Response(calendar_data)

class QnAViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QnASerializer

    def get_queryset(self):
        diary_id = self.kwargs.get('diary_id')
        return QnA.objects.filter(diary_id=diary_id, diary__user=self.request.user)

    def _update_stats(self, qnas, diary):
        """QnA 데이터를 기반으로 통계 업데이트"""
        today = date.today()
        
        # 카테고리별로 통계 계산
        for category, _ in Stats.CATEGORY_CHOICES:
            category_qnas = [
                qna for qna in qnas 
                if qna.question.lower().startswith(category.lower())
            ]
            
            if not category_qnas:
                continue
                
            # 정확도와 응답 시간 평균 계산
            accuracies = [qna.correctness for qna in category_qnas if qna.correctness is not None]
            response_times = [qna.response_time for qna in category_qnas if qna.response_time is not None]
            
            if accuracies or response_times:
                avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # 통계 저장 또는 업데이트
                Stats.objects.update_or_create(
                    user=diary.user,
                    stat_date=today,
                    category=category,
                    defaults={
                        'accuracy': round(avg_accuracy, 1),
                        'response_time': round(avg_response_time)
                    }
                )

    def create(self, request, *args, **kwargs):
        diary_id = self.kwargs.get('diary_id')
        diary = get_object_or_404(Diary, id=diary_id, user=request.user)
        
        qna_data = request.data if isinstance(request.data, list) else [request.data]
        serializer = self.get_serializer(data=qna_data, many=True)
        serializer.is_valid(raise_exception=True)
        
        qnas = [QnA(diary=diary, **item) for item in serializer.validated_data]
        created_qnas = QnA.objects.bulk_create(qnas)
        
        # 통계 업데이트
        self._update_stats(created_qnas, diary)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            qna = self.get_object()
            self._update_stats([qna], qna.diary)
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            qna = self.get_object()
            self._update_stats([qna], qna.diary)
        return response

class StatsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StatsSerializer

    def get_queryset(self):
        queryset = Stats.objects.filter(user=self.request.user)
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')
        category = self.request.query_params.get('category')

        if from_date:
            queryset = queryset.filter(stat_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(stat_date__lte=to_date)
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def _get_period_dates(self, period):
        today = date.today()
        if period == 'weekly':
            current_start = today - timedelta(days=today.weekday())
            current_end = current_start + timedelta(days=6)
            previous_start = current_start - timedelta(weeks=1)
            previous_end = previous_start + timedelta(days=6)
        else:  # monthly
            current_start = date(today.year, today.month, 1)
            current_end = today

            # 이전 달의 시작일과 마지막 날 계산
            if today.month == 1:
                previous_start = date(today.year - 1, 12, 1)
                previous_end = date(today.year - 1, 12, 31)
            else:
                previous_start = date(today.year, today.month - 1, 1)
                # 이전 달의 마지막 날 계산
                if today.month == 3:
                    # 2월인 경우 윤년 고려
                    previous_end = date(today.year, 2, 29 if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0) else 28)
                else:
                    # 나머지 달의 경우
                    last_day = {
                        4: 30, 6: 30, 9: 30, 11: 30,
                        1: 31, 3: 31, 5: 31, 7: 31, 8: 31, 10: 31, 12: 31
                    }[today.month - 1]
                    previous_end = date(today.year, today.month - 1, last_day)

        return current_start, current_end, previous_start, previous_end

    def _calculate_period_stats(self, start_date, end_date, category=None):
        queryset = Stats.objects.filter(
            user=self.request.user,
            stat_date__gte=start_date,
            stat_date__lte=end_date
        )
        
        if category:
            queryset = queryset.filter(category=category)

        stats = queryset.aggregate(
            avg_accuracy=Avg('accuracy'),
            avg_response_time=Avg('response_time')
        )

        return {
            'avg_accuracy': round(stats['avg_accuracy'] or 0, 1),
            'avg_response_time': round(stats['avg_response_time'] or 0)
        }

    @action(detail=False)
    def summary(self, request):
        period = request.query_params.get('period', 'monthly')
        category = request.query_params.get('category')
        
        # 현재 기간과 이전 기간의 날짜 범위 계산
        current_start, current_end, previous_start, previous_end = self._get_period_dates(period)
        
        # 현재 기간과 이전 기간의 통계 계산
        current_stats = self._calculate_period_stats(current_start, current_end, category)
        previous_stats = self._calculate_period_stats(previous_start, previous_end, category)

        # 카테고리별 통계 계산
        categories_data = []
        categories = [cat[0] for cat in Stats.CATEGORY_CHOICES]
        
        if category:
            categories = [category]
            
        for cat in categories:
            current_cat_stats = self._calculate_period_stats(current_start, current_end, cat)
            previous_cat_stats = self._calculate_period_stats(previous_start, previous_end, cat)
            
            categories_data.append({
                "category": cat,
                "avg_accuracy": current_cat_stats['avg_accuracy'],
                "delta_accuracy": round(
                    current_cat_stats['avg_accuracy'] - previous_cat_stats['avg_accuracy'], 1
                ),
                "avg_response_time": current_cat_stats['avg_response_time'],
                "delta_response_time": round(
                    current_cat_stats['avg_response_time'] - previous_cat_stats['avg_response_time']
                )
            })

        summary_data = {
            "period": current_start.strftime("%Y-%m"),
            "compare_to": previous_start.strftime("%Y-%m"),
            "categories": categories_data
        }
        
        serializer = StatsSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False)
    def categories(self, request):
        categories = [
            {"code": code, "label": label}
            for code, label in Stats.CATEGORY_CHOICES
        ]
        serializer = StatsCategorySerializer(categories, many=True)
        return Response(serializer.data)

def login_error(request):
    """
    Handle login errors and redirect to frontend with error message
    """
    error = request.GET.get('error', 'unknown_error')
    message = request.GET.get('message', '')
    
    # Redirect to frontend with error parameters
    frontend_url = 'https://localhost:5174'  # Vite development server
    return HttpResponseRedirect(f'{frontend_url}/login?error={error}&message={message}')