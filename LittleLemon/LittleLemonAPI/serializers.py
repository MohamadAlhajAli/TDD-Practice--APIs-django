from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from LittleLemonAPI.models import MenuItem 

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


class MenuItemSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = MenuItem 
        fields = ["id", "title"] 
        