from decimal import Decimal
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from LittleLemonAPI.models import MenuItem, Category

class RegistrationSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        max_length=254,
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            allowed_fields = {"username", "email", "password"}
            unexpected_fields = set(data) - allowed_fields

            if unexpected_fields:
                raise serializers.ValidationError({
                    field: ["This field is not allowed."]
                    for field in sorted(unexpected_fields)
                })

        return super().to_internal_value(data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "slug"]

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only = True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
    )
    price = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=Decimal("0.00"), max_value=Decimal("9999.99"),)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            allowed_fields = {"title", "price", "featured", "category_id"}
            unexpected_fields = set(data) - allowed_fields

            if unexpected_fields:
                raise serializers.ValidationError({
                    field: ["This field is not allowed."]
                    for field in sorted(unexpected_fields)
                })

            if self.instance is not None and not self.partial:
                missing_fields = allowed_fields - set(data)
                if missing_fields:
                    raise serializers.ValidationError({
                        field: ["This field is required."]
                        for field in sorted(missing_fields)
                    })

        return super().to_internal_value(data)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category", "category_id"]
