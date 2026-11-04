from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin_test',
            password='Password123!',
            email='admin@test.com',
            role=User.ROLE_ADMIN
        )
        self.seller = User.objects.create_user(
            username='seller_test',
            password='Password123!',
            email='seller@test.com',
            role=User.ROLE_SELLER
        )
        self.buyer = User.objects.create_user(
            username='buyer_test',
            password='Password123!',
            email='buyer@test.com',
            role=User.ROLE_BUYER
        )

    def test_user_roles(self):
        self.assertTrue(self.admin.is_admin_role)
        self.assertTrue(self.seller.is_seller_role)
        self.assertTrue(self.buyer.is_buyer_role)

    def test_register_buyer(self):
        payload = {
            'username': 'new_buyer',
            'email': 'newbuyer@example.com',
            'password': 'SafePassword123',
            'password_confirm': 'SafePassword123',
            'role': 'buyer',
            'phone_number': '1234567890',
            'address': '123 Market St'
        }
        response = self.client.post('/api/auth/register/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'buyer')
        self.assertEqual(response.data['user']['username'], 'new_buyer')

    def test_register_seller(self):
        payload = {
            'username': 'new_seller',
            'email': 'newseller@example.com',
            'password': 'SafePassword123',
            'password_confirm': 'SafePassword123',
            'role': 'seller',
        }
        response = self.client.post('/api/auth/register/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'seller')

    def test_register_password_mismatch(self):
        payload = {
            'username': 'mismatch_user',
            'password': 'SafePassword123',
            'password_confirm': 'DifferentPassword456',
            'role': 'buyer'
        }
        response = self.client.post('/api/auth/register/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'seller_test',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'seller')
        self.assertEqual(response.data['redirect_url'], '/seller-dashboard/')

    def test_login_invalid_credentials(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'seller_test',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_user_authenticated_and_logout(self):
        # Login
        self.client.login(username='buyer_test', password='Password123!')
        me_resp = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(me_resp.data['authenticated'])
        self.assertEqual(me_resp.data['user']['username'], 'buyer_test')

        # Logout
        logout_resp = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        # Me should now be unauthenticated
        me_after = self.client.get('/api/auth/me/')
        self.assertFalse(me_after.data['authenticated'])
