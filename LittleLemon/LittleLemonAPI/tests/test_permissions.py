
from rest_framework.response import Response 
from django.contrib.auth import get_user_model 
from django.contrib.auth.models import AnonymousUser, Group
from types import SimpleNamespace
from django.test import TestCase  
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView 
from LittleLemonAPI.permissions import (get_user_role, IsManager, IsDeliveryCrew, IsManagerOrReadOnly) 


class UserRoleTests(TestCase): 

    def test_user_without_role_group_is_customer(self): 

        user = get_user_model().objects.create_user(
              username = "customer", 
        )

        role = get_user_role(user) 

        self.assertEqual(
               role, 
               'Customer'
        )

    def test_anonymous_user_is_anonymous(self):
        user = AnonymousUser()

        role = get_user_role(user)

        self.assertEqual(role, "Anonymous")
      
    def test_superuser_is_manager(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Lemon!River82Cloud",
        )

        role = get_user_role(user)

        self.assertEqual(role, "Manager")
    
    def test_manager_group_member_is_manager(self):
        user = get_user_model().objects.create_user(
            username="maria",
        )
        manager_group = Group.objects.create(name="Manager")
        user.groups.add(manager_group)

        role = get_user_role(user)

        self.assertEqual(role, "Manager")
    
    def test_delivery_group_member_is_delivery_crew(self): 

        user = get_user_model().objects.create_user(
             username="sam", 
        )

        delivery_group = Group.objects.create(name="Delivery crew") 
        user.groups.add(delivery_group) 

        role = get_user_role(user) 

        self.assertEqual(role, "Delivery crew") 
    
    def test_manager_takes_precedence_over_delivery_crew(self): 

        user = get_user_model().objects.create_user(
            username = "dual_role", 
        )

        manager_group = Group.objects.create(name="Manager") 
        delivery_group = Group.objects.create(name="Delivery crew") 

        user.groups.add(manager_group, delivery_group) 

        role = get_user_role(user)

        self.assertEqual(role, "Manager") 
    
    def test_staff_only_user_is_customer(self):
        user = get_user_model().objects.create_user(
            username="staff_user",
            is_staff=True,
        )

        role = get_user_role(user)

        self.assertEqual(role, "Customer")

    def test_unrelated_group_member_is_customer(self):
        user = get_user_model().objects.create_user(
            username="other_group_user",
        )
        unrelated_group = Group.objects.create(name="Editors")
        user.groups.add(unrelated_group)
      
        role = get_user_role(user)

        self.assertEqual(role, "Customer")

class IsManagerTests(TestCase):
    def test_only_managers_are_allowed(self):
        manager = get_user_model().objects.create_user(
            username="maria",
        )
        manager.groups.add(Group.objects.create(name="Manager"))

        superuser = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Lemon!River82Cloud",
        )
        customer = get_user_model().objects.create_user(
            username="customer",
        )

        permission = IsManager()

        for user, expected in (
            (manager, True),
            (superuser, True),
            (customer, False),
            (AnonymousUser(), False),
        ):
            with self.subTest(user=str(user)):
                request = SimpleNamespace(user=user, method="POST")

                self.assertEqual(
                    permission.has_permission(request, view=None),
                    expected,
                )           

class IsDeliveryCrewTests(TestCase):
    def test_only_delivery_crew_members_are_allowed(self):
        delivery_user = get_user_model().objects.create_user(
            username="sam",
        )
        delivery_user.groups.add(
            Group.objects.create(name="Delivery crew")
        )

        manager = get_user_model().objects.create_user(
            username="maria",
        )
        manager.groups.add(Group.objects.create(name="Manager"))

        superuser = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Lemon!River82Cloud",
        )
        customer = get_user_model().objects.create_user(
            username="customer",
        )

        permission = IsDeliveryCrew()

        for user, expected in (
            (delivery_user, True),
            (manager, False),
            (superuser, False),
            (customer, False),
            (AnonymousUser(), False),
        ):
            with self.subTest(user=str(user)):
                request = SimpleNamespace(user=user, method="PATCH")

                self.assertEqual(
                    permission.has_permission(request, view=None),
                    expected,
                )

class IsManagerOrReadOnlyTests(TestCase):
    def test_reads_require_login_and_writes_require_manager(self):
        manager = get_user_model().objects.create_user(
            username="maria",
        )
        manager.groups.add(Group.objects.create(name="Manager"))

        delivery_user = get_user_model().objects.create_user(
            username="sam",
        )
        delivery_user.groups.add(
            Group.objects.create(name="Delivery crew")
        )

        customer = get_user_model().objects.create_user(
            username="customer",
        )

        permission = IsManagerOrReadOnly()

        cases = (
            (manager, "GET", True),
            (delivery_user, "GET", True),
            (customer, "GET", True),
            (AnonymousUser(), "GET", False),
            (manager, "POST", True),
            (delivery_user, "POST", False),
            (customer, "POST", False),
            (AnonymousUser(), "POST", False),
        )

        for user, method, expected in cases:
            with self.subTest(user=str(user), method=method):
                request = SimpleNamespace(user=user, method=method)

                self.assertEqual(
                    permission.has_permission(request, view=None),
                    expected,
                )

class PermissionResponseTests(TestCase):
    def test_manager_only_view_returns_expected_status_codes(self):
        class ManagerOnlyView(APIView):
            permission_classes = [IsManager]

            def get(self, request):
                return Response({"allowed": True})

        view = ManagerOnlyView.as_view()
        factory = APIRequestFactory()

        anonymous_response = view(factory.get("/permission-check/"))
        self.assertEqual(anonymous_response.status_code, 401)

        customer = get_user_model().objects.create_user(
            username="customer",
        )
        customer_request = factory.get("/permission-check/")
        force_authenticate(customer_request, user=customer)

        customer_response = view(customer_request)
        self.assertEqual(customer_response.status_code, 403)

        manager = get_user_model().objects.create_user(
            username="maria",
        )
        manager.groups.add(Group.objects.create(name="Manager"))
        manager_request = factory.get("/permission-check/")
        force_authenticate(manager_request, user=manager)

        manager_response = view(manager_request)
        self.assertEqual(manager_response.status_code, 200)



