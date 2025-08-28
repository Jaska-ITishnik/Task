from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import Notification

User = get_user_model()


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "id", "username", "email", "role", "phone", "specialty", "is_active", "date_joined"
        read_only_fields = "id", "role", "is_active", "date_joined"


class RegisterSerializer(ModelSerializer):
    password = CharField(write_only=True, validators=[validate_password])
    role = ChoiceField(choices=User.Role.choices, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role", "phone", "specialty")

    def create(self, validated_data):
        role = validated_data.pop("role", "client")
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.role = role
        if user.role == User.Role.ADMIN:
            user.is_staff = True
        user.save()
        return user


class LoginSerializer(Serializer):
    username = CharField()
    password = CharField()

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        username = validated_data.get('username')
        password = validated_data.get('password')
        user = authenticate(request=self.context.get('request'), username=username, password=password)
        if not user:
            raise ValidationError("Invalid username or password")
        return {"user": user}


class NotificationSerializer(ModelSerializer):
    sender_name = CharField(source="sender.username", read_only=True)
    receiver_name = CharField(source="receiver.username", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "sender", "sender_name",
            "receiver", "receiver_name",
            "message", "is_read", "created_at"
        ]
        read_only_fields = "id", "sender", "is_read", "created_at"
