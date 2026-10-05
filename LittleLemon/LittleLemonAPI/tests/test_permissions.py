from django.contrib.auth import get_user_model 
from django.contrib.auth.models import AnonymousUser, Group

from django.test import TestCase 

from LittleLemonAPI.permissions import get_user_role 


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