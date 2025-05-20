from rest_framework import serializers
from .models import User, Family, Diary, QnA, Stats

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['id', 'name', 'relationship', 'gender']
        read_only_fields = ['id']

    def validate_name(self, value):
        """이름이 빈 문자열이면 None으로 변환"""
        if value and value.strip():
            return value.strip()
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    families = FamilySerializer(many=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'name', 'birth_date', 'gender', 'families', 'is_profile_completed']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        families_data = validated_data.pop('families', None)
        
        # 사용자 정보 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 프로필이 완성되었는지 확인
        if instance.name and instance.birth_date and instance.gender:
            instance.is_profile_completed = True
        
        instance.save()

        # 가족 정보 업데이트
        if families_data is not None:
            instance.families.all().delete()  # 기존 가족 정보 삭제
            for family_data in families_data:
                Family.objects.create(user=instance, **family_data)

        return instance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'birth_date', 'gender', 'is_profile_completed']
        read_only_fields = ['id', 'username', 'email']

class QnASerializer(serializers.ModelSerializer):
    class Meta:
        model = QnA
        fields = ['id', 'diary', 'question', 'correct_answer', 'user_response', 'correctness', 'response_time']
        read_only_fields = ['id', 'diary']

class DiarySerializer(serializers.ModelSerializer):
    qna_count = serializers.SerializerMethodField()

    class Meta:
        model = Diary
        fields = ['id', 'user', 'diary_date', 'category', 'content', 'qna_count']
        read_only_fields = ['id', 'user']

    def get_qna_count(self, obj):
        return obj.qnas.count()

class DiaryDetailSerializer(DiarySerializer):
    qnas = QnASerializer(many=True, read_only=True)

    class Meta(DiarySerializer.Meta):
        fields = DiarySerializer.Meta.fields + ['qnas']

class StatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stats
        fields = ['id', 'user', 'stat_date', 'category', 'accuracy', 'response_time']
        read_only_fields = ['id', 'user']

class StatsSummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    compare_to = serializers.CharField()
    categories = serializers.ListField(child=serializers.DictField())

class StatsCategorySerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField() 