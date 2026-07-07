from rest_framework import serializers
from django.conf import settings
from .models import User, UserProfile, UserPhoto, Interest, Goal, OTPVerification
from apps.locations.models import Region, District


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name', 'name_uz', 'name_ru', 'icon']


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['id', 'name', 'name_uz', 'name_ru', 'icon']


class UserPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoto
        fields = ['id', 'image', 'is_main', 'order', 'created_at']
        read_only_fields = ['created_at']


class NestedRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'name_uz', 'name_ru']


class NestedDistrictSerializer(serializers.ModelSerializer):
    region = NestedRegionSerializer(read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'name_uz', 'name_ru', 'region']


class UserProfileSerializer(serializers.ModelSerializer):
    district = NestedDistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.locations.models', fromlist=['District']).District.objects.all(),
        source='district', write_only=True, required=False
    )
    interests = InterestSerializer(many=True, read_only=True)
    interest_ids = serializers.PrimaryKeyRelatedField(
        queryset=Interest.objects.all(), many=True, source='interests',
        write_only=True, required=False
    )
    goals = GoalSerializer(many=True, read_only=True)
    goal_ids = serializers.PrimaryKeyRelatedField(
        queryset=Goal.objects.all(), many=True, source='goals',
        write_only=True, required=False
    )
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'patronymic',
            'birth_date', 'age', 'gender', 'bio',
            'height', 'weight',
            'latitude', 'longitude',
            'district', 'district_id',
            'interests', 'interest_ids',
            'goals', 'goal_ids',
            'is_face_verified', 'is_complete',
        ]
        read_only_fields = ['is_face_verified', 'is_complete', 'age']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    photos = serializers.SerializerMethodField()
    main_photo = serializers.SerializerMethodField()
    subscription_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone',
            'is_email_verified', 'is_phone_verified',
            'profile', 'photos', 'main_photo',
            'subscription_type', 'is_online', 'last_seen', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_photos(self, obj):
        # Soft-delete qilingan rasmlar hech qachon clientga qaytarilmaydi
        photos = obj.photos.filter(is_deleted=False)
        return UserPhotoSerializer(photos, many=True, context=self.context).data

    def get_main_photo(self, obj):
        active = obj.photos.filter(is_deleted=False)
        photo = active.filter(is_main=True).first() or active.first()
        if photo:
            return UserPhotoSerializer(photo, context=self.context).data
        return None

    def get_subscription_type(self, obj):
        try:
            sub = getattr(obj, 'subscription', None)
            if sub and sub.is_active and sub.plan:
                return sub.plan.plan_type
        except Exception:
            pass
        return 'free'


# ── Auth serializers ──────────────────────────────────────────────

class SendOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email yoki telefon raqam")


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField(max_length=6)


class RegisterSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, attrs):
        identifier = attrs['identifier']
        otp_code = attrs['otp']
        record = OTPVerification.objects.filter(
            identifier=identifier, otp=otp_code
        ).order_by('-created_at').first()
        if not record or not record.is_valid():
            raise serializers.ValidationError({'otp': 'OTP noto\'g\'ri yoki muddati o\'tgan.'})
        attrs['_otp_record'] = record
        return attrs

    def create(self, validated_data):
        identifier = validated_data['identifier']
        password = validated_data['password']
        record = validated_data['_otp_record']
        record.is_used = True
        record.save()

        is_email = '@' in identifier
        kwargs = {'email': identifier} if is_email else {'phone': identifier}
        user, created = User.objects.get_or_create(**kwargs)
        if created:
            user.set_password(password)
        if is_email:
            user.is_email_verified = True
        else:
            user.is_phone_verified = True
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ProfileSetupSerializer(serializers.ModelSerializer):
    interest_ids = serializers.PrimaryKeyRelatedField(
        queryset=Interest.objects.all(), many=True, source='interests', required=False
    )
    goal_ids = serializers.PrimaryKeyRelatedField(
        queryset=Goal.objects.all(), many=True, source='goals', required=False
    )
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.locations.models', fromlist=['District']).District.objects.all(),
        source='district', required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'patronymic',
            'birth_date', 'gender', 'bio', 'height', 'weight',
            'latitude', 'longitude',
            'district_id', 'interest_ids', 'goal_ids',
        ]

    def create(self, validated_data):
        interests = validated_data.pop('interests', [])
        goals = validated_data.pop('goals', [])
        profile = UserProfile.objects.create(**validated_data)
        if interests:
            profile.interests.set(interests)
        if goals:
            profile.goals.set(goals)
        return profile

    def update(self, instance, validated_data):
        interests = validated_data.pop('interests', None)
        goals = validated_data.pop('goals', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if interests is not None:
            instance.interests.set(interests)
        if goals is not None:
            instance.goals.set(goals)
        return instance


class FaceScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['face_scan']

    def update(self, instance, validated_data):
        instance.face_scan = validated_data['face_scan']
        instance.is_face_verified = True   # Haqiqiy loyihada AI/liveness check
        instance.save()
        return instance


class PhotoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoto
        fields = ['image', 'is_main', 'order']

    def validate(self, attrs):
        user = self.context['request'].user
        if user.photos.filter(is_deleted=False).count() >= settings.MAX_USER_PHOTOS:
            raise serializers.ValidationError(
                f"Maksimal {settings.MAX_USER_PHOTOS} ta rasm yuklash mumkin."
            )
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return UserPhoto.objects.create(user=user, **validated_data)
