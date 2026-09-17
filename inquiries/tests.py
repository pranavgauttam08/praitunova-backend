from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Inquiry


@override_settings(
    ADMIN_NOTIFICATION_EMAIL='admin@example.com',
    DEFAULT_FROM_EMAIL='Test <test@example.com>',
)
class InquiryCreateTests(APITestCase):
    def setUp(self):
        self.url = reverse('inquiry_create')
        self.payload = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '9876543210',
            'company': 'Acme Corp',
            'service': 'Web Development',
            'message': 'We need a new website.',
        }

    def test_valid_submission_creates_inquiry_and_sends_email(self):
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Jane Doe', mail.outbox[0].subject)

    def test_missing_required_field_is_rejected(self):
        payload = {**self.payload}
        del payload['email']
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_honeypot_field_silently_drops_submission(self):
        payload = {**self.payload, 'website': 'https://spambot.example'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_anonymous_cannot_list_inquiries(self):
        response = self.client.get(reverse('inquiry_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_view_stats(self):
        response = self.client.get(reverse('inquiry_stats'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminInquiryTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username='admin', email='admin@example.com', password='S3curePass!23'
        )
        Inquiry.objects.create(name='Jane Doe', email='jane@example.com', message='Hi')
        Inquiry.objects.create(name='John Roe', email='john@example.com', message='Hello')

    def _login(self):
        response = self.client.post(
            reverse('token_obtain'),
            {'username': 'admin', 'password': 'S3curePass!23'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_can_list_inquiries_paginated(self):
        self._login()
        response = self.client.get(reverse('inquiry_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_admin_can_view_stats(self):
        self._login()
        response = self.client.get(reverse('inquiry_stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['new'], 2)

    def test_admin_can_update_status(self):
        self._login()
        inquiry = Inquiry.objects.first()
        response = self.client.patch(
            reverse('inquiry_detail', args=[inquiry.id]),
            {'status': 'CONTACTED'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, 'CONTACTED')

    def test_wrong_credentials_are_rejected(self):
        response = self.client.post(
            reverse('token_obtain'),
            {'username': 'admin', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthzTests(TestCase):
    def test_healthz_returns_ok(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
