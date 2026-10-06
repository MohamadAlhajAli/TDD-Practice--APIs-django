from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase
from LittleLemonAPI.models import Category, MenuItem, Order, OrderItem, Cart


class MenuListTests(APITestCase):
    def test_authenticated_user_can_list_menu_items(self):
        user = get_user_model().objects.create_user(username="customer")
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )

        self.client.force_authenticate(user=user)

        response = self.client.get("/api/menu-items")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data[0],
            {
                "id": item.id,
                "title": "Grilled fish",
                "price": "15.50",
                "featured": False,
                "category": {
                    "id": category.id,
                    "title": "Main courses",
                    "slug": "main-courses",
                },
            },
        )

class MenuCreateTests(APITestCase):
    def test_manager_can_create_menu_item(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Desserts",
            slug="desserts",
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            "/api/menu-items",
            {
                "title": "Lemon cake",
                "price": "8.50",
                "featured": True,
                "category_id": category.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = MenuItem.objects.get(title="Lemon cake")
        self.assertEqual(item.category, category)
    
    def test_customer_cannot_create_menu_item(self):
        customer = get_user_model().objects.create_user(username="customer")
        category = Category.objects.create(
            title="Desserts",
            slug="desserts",
        )
        self.client.force_authenticate(user=customer)

        response = self.client.post(
            "/api/menu-items",
            {
                "title": "Lemon cake",
                "price": "8.50",
                "featured": True,
                "category_id": category.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(MenuItem.objects.exists())

    def test_unknown_create_field_is_rejected(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Desserts",
            slug="desserts",
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            "/api/menu-items",
            {
                "title": "Lemon cake",
                "price": "8.50",
                "featured": True,
                "category_id": category.id,
                "unexpected": "not allowed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unexpected", response.data)
        self.assertFalse(MenuItem.objects.exists())    

    def test_negative_price_is_rejected(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Desserts",
            slug="desserts",
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            "/api/menu-items",
            {
                "title": "Lemon cake",
                "price": "-0.01",
                "category_id": category.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)
        self.assertFalse(MenuItem.objects.exists())
    
    def test_invalid_create_fields_are_rejected(self): 
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))

        category = Category.objects.create(
            title="Desserts",
            slug="desserts",
        )
        self.client.force_authenticate(user=manager)

        valid_payload = {
            "title": "Lemon cake",
            "price": "8.50",
            "category_id": category.id,
        }
        cases = [
            ({"title": ""}, "title"),
            ({"price": "10000.00"}, "price"),
            ({"price": "8.555"}, "price"),
            ({"category_id": 999999}, "category_id"),
        ]

        for changes, field in cases:
            with self.subTest(changes=changes):
                payload = valid_payload.copy()
                payload.update(changes)
                response = self.client.post(
                    "/api/menu-items", payload, format="json"
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
                self.assertFalse(MenuItem.objects.exists())


class MenuDetailTests(APITestCase):
    def test_authenticated_user_can_retrieve_menu_item(self):
        user = get_user_model().objects.create_user(username="customer")
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(f"/api/menu-items/{item.pk}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Grilled fish")

    def test_manager_can_partially_update_menu_item(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.patch(
            f"/api/menu-items/{item.pk}",
            {"price": "17.25"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.price, Decimal("17.25"))
        self.assertEqual(item.title, "Grilled fish")

    def test_put_requires_featured_field(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.put(
            f"/api/menu-items/{item.pk}",
            {
                "title": "Grilled fish",
                "price": "17.25",
                "category_id": category.id,
                # "featured" is deliberately missing.
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("featured", response.data)
        item.refresh_from_db()
        self.assertEqual(item.price, Decimal("15.50"))

    def test_manager_can_delete_menu_item(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.delete(f"/api/menu-items/{item.pk}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Deleted successfully."})
        self.assertFalse(MenuItem.objects.filter(pk=item.pk).exists())

    def test_menu_item_in_order_cannot_be_deleted(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        order = Order.objects.create(user=manager, total=Decimal("15.50"))
        order_item = OrderItem.objects.create(
            order=order,
            menuitem=item,
            quantity=1,
            unit_price=Decimal("15.50"),
            price=Decimal("15.50"),
        )
        self.client.force_authenticate(user=manager)

        response = self.client.delete(f"/api/menu-items/{item.pk}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertTrue(MenuItem.objects.filter(pk=item.pk).exists())
        self.assertTrue(OrderItem.objects.filter(pk=order_item.pk).exists())
            
    def test_deleting_menu_item_removes_its_cart_rows(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        cart = Cart.objects.create(
            user=manager,
            menuitem=item,
            quantity=1,
            unit_price=Decimal("15.50"),
            price=Decimal("15.50"),
        )
        self.client.force_authenticate(user=manager)

        response = self.client.delete(f"/api/menu-items/{item.pk}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(MenuItem.objects.filter(pk=item.pk).exists())
        self.assertFalse(Cart.objects.filter(pk=cart.pk).exists())


