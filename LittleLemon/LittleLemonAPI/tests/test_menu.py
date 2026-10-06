from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from LittleLemonAPI.models import Category, MenuItem


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

