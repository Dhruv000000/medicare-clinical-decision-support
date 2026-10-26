import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile


@pytest.mark.django_db
class TestAuthentication:
    def test_registration_success(self):
        client = APIClient()
        payload = {
            "email": "testpatient@medicare.local",
            "password": "StrongPassword123!",
            "first_name": "Alice",
            "last_name": "Smith",
            "role": "patient",
        }
        response = client.post("/api/v1/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "testpatient@medicare.local"
        assert data["user"]["role"] == "patient"
        assert "tokens" in data
        assert "access" in data["tokens"]
        assert "refresh" in data["tokens"]
        assert "password" not in data["user"]

        # Ensure PatientProfile was auto-created
        user = User.objects.get(email="testpatient@medicare.local")
        assert PatientProfile.objects.filter(user=user).exists()

    def test_registration_duplicate_email(self):
        User.objects.create_user(
            email="existing@medicare.local",
            password="StrongPassword123!",
            role="patient",
        )
        client = APIClient()
        payload = {
            "email": "existing@medicare.local",
            "password": "AnotherPassword123!",
            "role": "patient",
        }
        response = client.post("/api/v1/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_registration_invalid_password(self):
        client = APIClient()
        payload = {
            "email": "shortpass@medicare.local",
            "password": "123",
            "role": "patient",
        }
        response = client.post("/api/v1/auth/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_login_success(self):
        User.objects.create_user(
            email="loginuser@medicare.local",
            password="StrongPassword123!",
            role="patient",
            first_name="Bob",
        )
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "loginuser@medicare.local", "password": "StrongPassword123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert "user" in data
        assert data["user"]["role"] == "patient"

    def test_login_invalid_credentials(self):
        User.objects.create_user(
            email="loginfail@medicare.local",
            password="StrongPassword123!",
            role="patient",
        )
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "loginfail@medicare.local", "password": "WrongPassword!"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "error" in data

    def test_token_refresh(self):
        User.objects.create_user(
            email="refreshuser@medicare.local",
            password="StrongPassword123!",
            role="patient",
        )
        client = APIClient()
        login_res = client.post(
            "/api/v1/auth/login/",
            {"email": "refreshuser@medicare.local", "password": "StrongPassword123!"},
            format="json",
        )
        refresh_token = login_res.json()["refresh"]

        refresh_res = client.post("/api/v1/auth/refresh/", {"refresh": refresh_token}, format="json")
        assert refresh_res.status_code == status.HTTP_200_OK
        assert "access" in refresh_res.json()

    def test_logout_and_blacklisting(self):
        User.objects.create_user(
            email="logoutuser@medicare.local",
            password="StrongPassword123!",
            role="patient",
        )
        client = APIClient()
        login_res = client.post(
            "/api/v1/auth/login/",
            {"email": "logoutuser@medicare.local", "password": "StrongPassword123!"},
            format="json",
        )
        tokens = login_res.json()
        access_token = tokens["access"]
        refresh_token = tokens["refresh"]

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_res = client.post("/api/v1/auth/logout/", {"refresh": refresh_token}, format="json")
        assert logout_res.status_code == status.HTTP_200_OK

        # Trying to refresh with the blacklisted token must fail
        reuse_res = client.post("/api/v1/auth/refresh/", {"refresh": refresh_token}, format="json")
        assert reuse_res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_and_role_escalation_prevention(self):
        user = User.objects.create_user(
            email="meuser@medicare.local",
            password="StrongPassword123!",
            role="patient",
            first_name="Jane",
            last_name="Doe",
        )
        PatientProfile.objects.create(user=user)

        client = APIClient()
        login_res = client.post(
            "/api/v1/auth/login/",
            {"email": "meuser@medicare.local", "password": "StrongPassword123!"},
            format="json",
        )
        access_token = login_res.json()["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # GET /me/
        me_res = client.get("/api/v1/auth/me/")
        assert me_res.status_code == status.HTTP_200_OK
        data = me_res.json()
        assert data["email"] == "meuser@medicare.local"
        assert data["role"] == "patient"
        assert "profile" in data

        # PATCH /me/ updating first_name
        patch_res = client.patch("/api/v1/auth/me/", {"first_name": "Janet", "role": "admin"}, format="json")
        assert patch_res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Janet"
        # Verify role was NOT escalated (Correction 11)
        assert user.role == "patient"

    def test_login_with_matching_role_succeeds(self):
        User.objects.create_user(
            email="role_patient@medicare.local",
            password="StrongPassword123!",
            role="patient",
            first_name="Pat",
        )
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "role_patient@medicare.local", "password": "StrongPassword123!", "role": "patient"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user"]["role"] == "patient"
        assert "access" in data

    def test_login_with_mismatched_role_fails(self):
        User.objects.create_user(
            email="role_patient2@medicare.local",
            password="StrongPassword123!",
            role="patient",
        )
        client = APIClient()
        # Attempt to log in with role='doctor' on a patient account
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "role_patient2@medicare.local", "password": "StrongPassword123!", "role": "doctor"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "role" in data["error"]["details"]

    def test_doctor_login_with_mismatched_role_fails(self):
        User.objects.create_user(
            email="role_doctor@medicare.local",
            password="StrongPassword123!",
            role="doctor",
        )
        client = APIClient()
        # Attempt to log in with role='patient' on a doctor account
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "role_doctor@medicare.local", "password": "StrongPassword123!", "role": "patient"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "role" in data["error"]["details"]

