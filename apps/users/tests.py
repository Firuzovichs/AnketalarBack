import hashlib
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.home.models import StaticPage
from .models import OTPVerification, TermsAcceptance, User, UserProfile
from .serializers import FaceScanSerializer, ProfileSetupSerializer


class TermsRegistrationTests(APITestCase):
    def setUp(self):
        self.terms, _ = StaticPage.objects.update_or_create(
            slug='terms',
            defaults={
                'title': 'Foydalanish shartlari',
                'version': '1.0',
                'content': 'Sinov uchun foydalanish shartlari.',
            },
        )
        self.register_url = reverse('register')

    def _create_otp(self, identifier='new@example.com', code='123456'):
        return OTPVerification.objects.create(
            identifier=identifier,
            otp=code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def test_registration_requires_explicit_terms_acceptance(self):
        response = self.client.post(self.register_url, {
            'identifier': 'new@example.com',
            'otp': '123456',
            'password': 'strong-password',
            'terms_accepted': False,
            'terms_version': self.terms.version,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('terms_accepted', response.data)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_registration_rejects_stale_terms_version(self):
        response = self.client.post(self.register_url, {
            'identifier': 'new@example.com',
            'otp': '123456',
            'password': 'strong-password',
            'terms_accepted': True,
            'terms_version': '0.9',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('terms_version', response.data)

    def test_registration_stores_terms_audit_record(self):
        otp = self._create_otp()
        response = self.client.post(self.register_url, {
            'identifier': 'new@example.com',
            'otp': '123456',
            'password': 'strong-password',
            'terms_accepted': True,
            'terms_version': self.terms.version,
        }, format='json', REMOTE_ADDR='127.0.0.1', HTTP_USER_AGENT='AnketalarTests/1.0')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        acceptance = TermsAcceptance.objects.get(user__email='new@example.com')
        self.assertEqual(acceptance.version, self.terms.version)
        self.assertEqual(
            acceptance.content_hash,
            hashlib.sha256(self.terms.content.encode('utf-8')).hexdigest(),
        )
        self.assertEqual(acceptance.ip_address, '127.0.0.1')
        self.assertEqual(acceptance.user_agent, 'AnketalarTests/1.0')
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_existing_user_can_accept_current_terms(self):
        user = User.objects.create_user(email='existing@example.com', password='password')
        self.client.force_authenticate(user)

        response = self.client.post(reverse('terms-accept'), {
            'terms_version': self.terms.version,
        }, format='json', REMOTE_ADDR='127.0.0.1', HTTP_USER_AGENT='AnketalarMobile/1.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['accepted'])
        acceptance = TermsAcceptance.objects.get(user=user)
        self.assertEqual(acceptance.version, self.terms.version)
        self.assertEqual(acceptance.user_agent, 'AnketalarMobile/1.0')


class AdultOnlyProfileTests(APITestCase):
    def test_profile_rejects_user_under_18(self):
        today = timezone.localdate()
        birth_date = today.replace(year=today.year - 17)
        serializer = ProfileSetupSerializer(data={
            'first_name': 'Test',
            'last_name': 'User',
            'birth_date': birth_date,
            'gender': 'M',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('birth_date', serializer.errors)


class ProfileSocialNicknameTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='social@example.com', password='password')
        self.profile = UserProfile.objects.create(
            user=self.user,
            first_name='Social',
            last_name='User',
            birth_date=timezone.localdate().replace(year=timezone.localdate().year - 22),
            gender='F',
        )
        self.client.force_authenticate(self.user)

    def test_profile_patch_updates_social_nicknames(self):
        response = self.client.patch(reverse('profile-setup'), {
            'social_tiktok': '@tiktok.user',
            'social_instagram': 'instagram_user',
            'social_telegram': 'telegram_user',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.social_tiktok, 'tiktok.user')
        self.assertEqual(self.profile.social_instagram, 'instagram_user')
        self.assertEqual(self.profile.social_telegram, 'telegram_user')

    def test_profile_rejects_social_profile_url(self):
        response = self.client.patch(reverse('profile-setup'), {
            'social_instagram': 'https://instagram.com/test_user',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('social_instagram', response.data)


class BiometricConsentTests(APITestCase):
    def test_face_scan_requires_separate_biometric_consent(self):
        user = User.objects.create_user(email='face@example.com', password='password')
        profile = UserProfile.objects.create(
            user=user,
            first_name='Face',
            last_name='Test',
            birth_date=timezone.localdate().replace(year=timezone.localdate().year - 20),
            gender='F',
        )
        serializer = FaceScanSerializer(
            profile,
            data={'biometric_consent': False},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('biometric_consent', serializer.errors)
