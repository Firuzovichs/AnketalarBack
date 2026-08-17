import hashlib
import re

from django.utils.html import urlize
from rest_framework import serializers

from apps.users.models import TermsAcceptance
from .models import Banner, News, StaticPage


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ['id', 'title', 'description', 'image', 'link_url', 'order']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class StaticPageSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    linked_content = serializers.SerializerMethodField()
    terms_banner = serializers.SerializerMethodField()

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

    class Meta:
        model = StaticPage
        fields = [
            'slug',
            'title',
            'version',
            'content',
            'linked_content',
            'links',
            'terms_banner',
            'updated_at',
        ]

    def get_links(self, obj):
        # Faqat foydalanish bo'limi va boshqa sahifalarda ham to'g'ri ssilkalar
        # chiqsin deb, matndan URL larni ajratib olamiz.
        return sorted(set(re.findall(r'https?://[^\s\)\]\}]+', obj.content)))

    def get_linked_content(self, obj):
        # Klient HTML ko'rinishda render qilsa, ssilkalar alohida ko'rinadi va bosiladi.
        return urlize(obj.content, trim_url_limit=None, nofollow=True, autoescape=True)

    def get_terms_banner(self, obj):
        request = self.context.get('request')
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return None
        if obj.slug != 'terms':
            return None

        user = request.user
        latest_terms = (
            TermsAcceptance.objects
            .filter(user=user)
            .order_by('-accepted_at')
            .first()
        )
        content_hash = hashlib.sha256(obj.content.encode('utf-8')).hexdigest()
        current_version_accepted = (
            latest_terms is not None
            and latest_terms.version == obj.version
            and latest_terms.content_hash == content_hash
        )

        try:
            profile = user.profile
        except Exception:
            profile = None
        return {
            'is_current_version_accepted': current_version_accepted,
            'requires_reaccept': latest_terms is not None and not current_version_accepted,
            'accepted_at': latest_terms.accepted_at if latest_terms else None,
            'accepted_version': latest_terms.version if latest_terms else None,
            'accepted_hash': latest_terms.content_hash if latest_terms else None,
            'legal_links': sorted(set(re.findall(r'https?://[^\s\)\]\}<>\"]+', obj.content))),
            'proof_media': self._build_proof_media(profile, request),
        }

class NewsSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ['id', 'title', 'description', 'content', 'image', 'published_at']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None
