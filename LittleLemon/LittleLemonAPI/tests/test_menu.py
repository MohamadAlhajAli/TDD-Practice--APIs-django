from requests import Response
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

class MenuAccessTests(APITestCase):
    def setUp(self):
        category = Category.objects.create(
            title="Main courses",
            slug="main-courses",
        )
        self.item = MenuItem.objects.create(
            title="Grilled fish",
            price=Decimal("15.50"),
            category=category,
        )
        self.category = category

    def test_anonymous_requests_return_401(self):
        detail = f"/api/menu-items/{self.item.pk}"
        payload = {
            "title": "Grilled fish",
            "price": "15.50",
            "featured": False,
            "category_id": self.category.pk,
        }
        responses = [
            ("list GET", self.client.get("/api/menu-items")),
            ("list POST", self.client.post(
                "/api/menu-items", payload, format="json"
            )),
            ("detail GET", self.client.get(detail)),
            ("detail PUT", self.client.put(detail, payload, format="json")),
            ("detail PATCH", self.client.patch(
                detail, {"price": "17.25"}, format="json"
            )),
            ("detail DELETE", self.client.delete(detail)),
        ]

        for name, response in responses:
            with self.subTest(name=name):
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

        self.assertTrue(MenuItem.objects.filter(pk=self.item.pk).exists())

    def test_customer_and_delivery_can_read_but_cannot_write(self):
        customer = get_user_model().objects.create_user(username="customer")
        delivery = get_user_model().objects.create_user(username="delivery")
        delivery.groups.add(Group.objects.create(name="Delivery crew"))

        detail = f"/api/menu-items/{self.item.pk}"
        payload = {
            "title": "Changed fish",
            "price": "17.25",
            "featured": True,
            "category_id": self.category.pk,
        }

        for role, user in (("Customer", customer), ("Delivery crew", delivery)):
            self.client.force_authenticate(user=user)

            cases = [
                ("list GET", self.client.get("/api/menu-items"), 200),
                ("detail GET", self.client.get(detail), 200),
                ("list POST", self.client.post(
                    "/api/menu-items", payload, format="json"
                ), 403),
                ("detail PUT", self.client.put(
                    detail, payload, format="json"
                ), 403),
                ("detail PATCH", self.client.patch(
                    detail, {"price": "17.25"}, format="json"
                ), 403),
                ("detail DELETE", self.client.delete(detail), 403),
            ]

            for action, response, expected in cases:
                with self.subTest(role=role, action=action):
                    self.assertEqual(response.status_code, expected)

        self.assertEqual(MenuItem.objects.count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Grilled fish")
        self.assertEqual(self.item.price, Decimal("15.50"))

    def test_superuser_has_manager_menu_access_without_group(self):
        admin = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Lemon!River82Cloud",
        )
        self.assertFalse(admin.groups.exists())
        self.client.force_authenticate(user=admin)

        self.assertEqual(self.client.get("/api/menu-items").status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/menu-items/{self.item.pk}").status_code,
            200,
        )

        created = self.client.post(
            "/api/menu-items",
            {
                "title": "Lemon tart",
                "price": "8.50",
                "featured": True,
                "category_id": self.category.pk,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        detail = f"/api/menu-items/{created.data['id']}"

        updated = self.client.put(
            detail,
            {
                "title": "Lemon tart",
                "price": "9.00",
                "featured": False,
                "category_id": self.category.pk,
            },
            format="json",
        )
        self.assertEqual(updated.status_code, 200)

        patched = self.client.patch(
            detail, {"price": "10.00"}, format="json"
        )
        self.assertEqual(patched.status_code, 200)

        deleted = self.client.delete(detail)
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(
            MenuItem.objects.filter(pk=created.data["id"]).exists()
        )

    def test_unknown_menu_item_id_returns_404(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        self.client.force_authenticate(user=manager)

        missing_id = self.item.pk + 1
        detail = f"/api/menu-items/{missing_id}"
        payload = {
            "title": "Grilled fish",
            "price": "15.50",
            "featured": False,
            "category_id": self.category.pk,
        }
        cases = [
            ("GET", self.client.get(detail)),
            ("PUT", self.client.put(detail, payload, format="json")),
            ("PATCH", self.client.patch(
                detail, {"price": "17.25"}, format="json"
            )),
            ("DELETE", self.client.delete(detail)),
        ]

        for method, response in cases:
            with self.subTest(method=method):
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(MenuItem.objects.count(), 1)

    def test_menu_item_validation_rejects_bad_data(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        self.client.force_authenticate(user=manager)

        invalid_payload = {
            "title": "",
            "price": "invalid",
            "featured": True,
            "category_id": self.category.pk,
        }
        response = self.client.post(
            "/api/menu-items", invalid_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("price", response.data)
        self.assertTrue(response.data["title"])
        self.assertTrue(response.data["price"])
        self.assertFalse(MenuItem.objects.filter(title="").exists())

    def test_create_defaults_featured_to_false(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        category = Category.objects.create(
            title="Desserts", slug="desserts"
        )
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            "/api/menu-items",
            {
                "title": "Lemon cake",
                "price": "8.50",
                "category_id": category.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = MenuItem.objects.get(pk=response.data["id"])
        self.assertFalse(item.featured)
        self.assertIs(response.data["featured"], False)

    def test_create_requires_category_id(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        self.client.force_authenticate(user=manager)

        response = self.client.post(
            "/api/menu-items",
            {"title": "Lemon cake", "price": "8.50"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id", response.data)
        self.assertEqual(MenuItem.objects.count(), 1)
        self.assertFalse(MenuItem.objects.filter(title="Lemon cake").exists())

    def test_manager_patch_rejects_invalid_fields_without_changes(self):
        manager = get_user_model().objects.create_user(username="manager")
        manager.groups.add(Group.objects.create(name="Manager"))
        self.client.force_authenticate(user=manager)

        cases = [
            ({"id": 999}, "id"),
            ({"category": {"id": self.category.pk}}, "category"),
            ({"category_id": 999999}, "category_id"),
            ({"price": "-0.01"}, "price"),
        ]

        for payload, field in cases:
            with self.subTest(payload=payload):
                response = self.client.patch(
                    f"/api/menu-items/{self.item.pk}",
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
                self.item.refresh_from_db()
                self.assertEqual(self.item.price, Decimal("15.50"))
                self.assertEqual(self.item.category_id, self.category.pk)

        self.assertEqual(MenuItem.objects.count(), 1)
