from requests import Response
from time import struct_time
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from rest_framework.authtoken.models import Token 


class RegistrationTests(APITestCase):
    def test_valid_registration_creates_normal_user(self):
        payload = {
            "username": "customer",
            "email": "customer@example.com",
            "password": "Lemon!River82Cloud",
        }

        response = self.client.post(
            "/api/users",
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = get_user_model().objects.get(
            username=payload["username"],
        )

        self.assertEqual(user.email, payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.groups.exists())
        self.assertNotIn("password", response.data)

    def test_registration_without_email_is_rejected(self): 

        payload = {
            'username': 'customer', 
            'password': 'Lemon!River82Cloud', 
        }   

        response = self.client.post(
            "/api/users",
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code, 
            status.HTTP_400_BAD_REQUEST, 
        )

        self.assertIn( "email", response.data) 
        
        self.assertFalse(
              get_user_model().objects.filter(
                   username = payload['username'], 
              ).exists()
        )
    
    def test_blank_and_invalid_emails_are_rejected(self):
        for email in ("", "not-an-email", None):
            with self.subTest(email=email):
                payload = {
                    "username": "customer",
                    "email": email,
                    "password": "Lemon!River82Cloud",
                }

                response = self.client.post(
                    "/api/users",
                    data=payload,
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn("email", response.data)
                self.assertFalse(
                    get_user_model().objects.filter(
                        username=payload["username"],
                    ).exists()
                )
 
    def test_privileged_and_unexpected_fields_are_rejected(self):
        extra_fields = {
            "is_staff": True,
            "is_superuser": True,
            "groups": [],
            "unexpected_field": "example",
        }

        for index, (field, value) in enumerate(extra_fields.items()):
            with self.subTest(field=field):
                username = f"customer{index}"
                payload = {
                    "username": username,
                    "email": f"{username}@example.com",
                    "password": "Lemon!River82Cloud",
                    field: value,
                }

                response = self.client.post(
                    "/api/users",
                    data=payload,
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn(field, response.data)
                self.assertFalse(
                    get_user_model().objects.filter(
                        username=username,
                    ).exists()
                )
          
    def test_weak_password_is_rejected(self):
        payload = {
            "username": "customer",
            "email": "customer@example.com",
            "password": "123",
        }

        response = self.client.post(
            "/api/users",
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("password", response.data)
        self.assertFalse(
            get_user_model().objects.filter(
                username=payload["username"],
            ).exists()
        )

    def test_duplicate_username_is_rejected(self):
        
        existing_user = get_user_model().objects.create_user(
            username="customer",
            email="original@example.com",
            password="Original!River82Cloud",
        )

        payload = {
            "username": "customer",
            "email": "replacement@example.com",
            "password": "Different!River82Cloud",
        }

        response = self.client.post(
            "/api/users",
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("username", response.data)
        self.assertEqual(
            get_user_model().objects.filter(
                username="customer",
            ).count(),
            1,
        )

        existing_user.refresh_from_db()
        self.assertEqual(
            existing_user.email,
            "original@example.com",
        )
        self.assertTrue(
            existing_user.check_password("Original!River82Cloud")
        )

class TokenLoginTests(APITestCase):
    
    def setUp(self):
        self.password = "Lemon!River82Cloud"
        self.user = get_user_model().objects.create_user(
            username="customer",
            email="customer@example.com",
            password=self.password,
        )

    def test_valid_credentials_return_user_token(self):
        response = self.client.post(
            "/token/login/",
            data={
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("auth_token", response.data)

        token = Token.objects.get(
            key=response.data["auth_token"],
        )
        self.assertEqual(token.user_id, self.user.pk)
    
    def test_invalid_credentials_are_rejected(self):
        invalid_credentials = [
            {
                "username": self.user.username,
                "password": "Wrong!Password82",
            },
            {
                "username": "unknown-user",
                "password": self.password,
            },
        ]

        for credentials in invalid_credentials:
            with self.subTest(username=credentials["username"]):
                response = self.client.post(
                    "/token/login/",
                    data=credentials,
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertNotIn("auth_token", response.data)
                self.assertFalse(Token.objects.exists())

class CurrentUserTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer",
            email="customer@example.com",
            password="Lemon!River82Cloud",
        )
        self.token = Token.objects.create(user=self.user)

    def test_valid_token_returns_current_user(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get("/api/users/users/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["id"], self.user.pk)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertNotIn("password", response.data)
    

    def test_missing_token_is_rejected(self):
        response = self.client.get("/api/users/users/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(response["WWW-Authenticate"], "Token")
        self.assertNotIn("username", response.data)
    
    def test_invalid_token_is_rejected(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token invalid-token",
        )

        response = self.client.get("/api/users/users/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertNotIn("username", response.data)


    def test_session_login_without_token_is_rejected(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        self.client.force_login(self.user)

        response = self.client.get("/api/users/users/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(response["WWW-Authenticate"], "Token")
        self.assertNotIn("username", response.data)
    
    



        
    

