import hashlib
import re

from django.db import transaction
from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from django.utils.html import urlize

from .models import User, UserProfile, UserPhoto, Interest, Goal, OTPVerification, TermsAcceptance
from apps.home.models import StaticPage
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
            'social_tiktok', 'social_instagram', 'social_telegram',
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
    terms_status = serializers.SerializerMethodField()

    @staticmethod
    def _build_proof_media(profile, request):
        if not profile or not request:
            return {
                'type': None,
                'url': None,
                'thumbnail_url': None,
                'is_face_verified': False,
                'biometric_consent_at': None,
                'biometric_consent_version': '',
            }

        media_url = None
        media_type = None
        thumbnail_url = None

        if profile.face_scan:
            try:
                thumbnail_url = request.build_absolute_uri(profile.face_scan.url)
            except Exception:
                thumbnail_url = None

        if getattr(profile, 'face_scan_video', None):
            try:
                media_url = request.build_absolute_uri(profile.face_scan_video.url)
                media_type = 'video'
            except Exception:
                media_url = None
                media_type = None

        if media_url is None and profile.face_scan:
            try:
                media_url = request.build_absolute_uri(profile.face_scan.url)
                media_type = 'image'
            except Exception:
                media_url = None
                media_type = None

        return {
            'type': media_type,
            'url': media_url,
            'thumbnail_url': thumbnail_url,
            'is_face_verified': bool(profile.is_face_verified),
            'biometric_consent_at': profile.biometric_consent_at,
            'biometric_consent_version': profile.biometric_consent_version,
        }

    @staticmethod
    def _extract_links(text):
        if not text:
            return []
        links = re.findall(r'https?://[^\s\)\]\}<>\"]+', text)
        return sorted(set([link.rstrip('.,;:!?)]}>') for link in links]))

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone',
            'is_email_verified', 'is_phone_verified',
            'profile', 'photos', 'main_photo',
            'subscription_type', 'is_online', 'last_seen', 'created_at',
            'terms_status',
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

    def get_terms_status(self, obj):
        request = self.context.get('request')
        try:
            profile = obj.profile
        except Exception:
            profile = None

        try:
            terms = StaticPage.objects.get(slug='terms')
        except StaticPage.DoesNotExist:
            return None

        latest = (
            TermsAcceptance.objects
            .filter(user=obj)
            .order_by('-accepted_at')
            .first()
        )
        current_hash = hashlib.sha256(terms.content.encode('utf-8')).hexdigest()
        accepted_current = bool(
            latest and latest.version == terms.version and latest.content_hash == current_hash
        )

        return {
            'is_current_version_accepted': accepted_current,
            'requires_reaccept': latest is not None and not accepted_current,
            'needs_accept': latest is None,
            'terms_version': terms.version,
            'terms_page_title': terms.title,
            'accepted_at': latest.accepted_at if latest else None,
            'accepted_version': latest.version if latest else None,
            'proof_media': self._build_proof_media(profile, request),
            'legal_links': sorted(set(re.findall(r'https?://[^\s<>"]+', terms.content))),
            'highlightable_content': urlize(terms.content, trim_url_limit=None, autoescape=True),
        }


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
    terms_accepted = serializers.BooleanField(write_only=True)
    terms_version = serializers.CharField(max_length=20, write_only=True)

    def validate(self, attrs):
        if not attrs['terms_accepted']:
            raise serializers.ValidationError({
                'terms_accepted': "Ro'yxatdan o'tish uchun foydalanish shartlariga rozilik berish shart."
            })

        try:
            terms_page = StaticPage.objects.get(slug='terms')
        except StaticPage.DoesNotExist:
            raise serializers.ValidationError({
                'terms_accepted': 'Foydalanish shartlari vaqtincha mavjud emas.'
            })

        if attrs['terms_version'] != terms_page.version:
            raise serializers.ValidationError({
                'terms_version': (
                    "Foydalanish shartlari yangilangan. Yangi matnni o'qib, "
                    f"{terms_page.version} versiyaga rozilik bering."
                )
            })

        identifier = attrs['identifier']
        otp_code = attrs['otp']
        record = OTPVerification.objects.filter(
            identifier=identifier, otp=otp_code
        ).order_by('-created_at').first()
        if not record or not record.is_valid():
            raise serializers.ValidationError({'otp': 'OTP noto\'g\'ri yoki muddati o\'tgan.'})
        attrs['_otp_record'] = record
        attrs['_terms_page'] = terms_page
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        identifier = validated_data['identifier']
        password = validated_data['password']
        record = validated_data['_otp_record']
        terms_page = validated_data['_terms_page']
        record.is_used = True
        record.save(update_fields=['is_used'])

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

        request = self.context.get('request')
        ip_address = request.META.get('REMOTE_ADDR') if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        TermsAcceptance.objects.get_or_create(
            user=user,
            version=terms_page.version,
            content_hash=hashlib.sha256(terms_page.content.encode('utf-8')).hexdigest(),
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
            },
        )
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
            'social_tiktok', 'social_instagram', 'social_telegram',
            'latitude', 'longitude',
            'district_id', 'interest_ids', 'goal_ids',
        ]

    def validate_birth_date(self, value):
        today = timezone.localdate()
        try:
            adult_cutoff = today.replace(year=today.year - 18)
        except ValueError:
            adult_cutoff = today.replace(year=today.year - 18, day=28)
        if value > adult_cutoff:
            raise serializers.ValidationError("Anketalar xizmatidan faqat 18 yoshga to'lganlar foydalanishi mumkin.")
        return value

    @staticmethod
    def _validate_social_nickname(value, network):
        """Store only a social nickname, never a full profile URL."""
        value = (value or '').strip()
        if not value:
            return ''

        lowered = value.lower()
        if '://' in lowered or '/' in value or '?' in value or '#' in value:
            raise serializers.ValidationError(
                "Faqat nickname yozing. Havola kiritish kerak emas."
            )

        nickname = value.lstrip('@').strip()
        patterns = {
            'tiktok': r'^[A-Za-z0-9._]{2,24}$',
            'instagram': r'^[A-Za-z0-9._]{1,30}$',
            'telegram': r'^[A-Za-z0-9_]{5,32}$',
        }
        if not re.fullmatch(patterns[network], nickname):
            raise serializers.ValidationError(
                "Nickname formati noto‘g‘ri. Faqat lotin harflari, raqam, nuqta yoki pastki chiziqdan foydalaning."
            )
        return nickname

    def validate_social_tiktok(self, value):
        return self._validate_social_nickname(value, 'tiktok')

    def validate_social_instagram(self, value):
        return self._validate_social_nickname(value, 'instagram')

    def validate_social_telegram(self, value):
        return self._validate_social_nickname(value, 'telegram')

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
    BIOMETRIC_CONSENT_VERSION = '1.0'
    biometric_consent = serializers.BooleanField(write_only=True)

    class Meta:
        model = UserProfile
        fields = ['face_scan', 'biometric_consent']

    def validate(self, attrs):
        if not attrs.pop('biometric_consent', False):
            raise serializers.ValidationError({
                'biometric_consent': "Yuz tasviriga ishlov berish uchun alohida rozilik berish shart."
            })
        if not attrs.get('face_scan'):
            raise serializers.ValidationError({'face_scan': 'Yuz tasvirini yuborish shart.'})
        return attrs

    def update(self, instance, validated_data):
        instance.face_scan = validated_data['face_scan']
        instance.is_face_verified = True   # Haqiqiy loyihada AI/liveness check
        instance.biometric_consent_at = timezone.now()
        instance.biometric_consent_version = self.BIOMETRIC_CONSENT_VERSION
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
