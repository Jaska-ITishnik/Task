from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.models import Notification
from apps.permissions import IsAdminRole
from apps.serializers.user_serializers import UserSerializer, NotificationSerializer

User = get_user_model()


@extend_schema(tags=['User'], description="Foydalanuvchi o'z profilini ko'rishi/yangilashi uchun API")
class MeView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=['User'], description="Admin boshqa foydalanuvchilarni ko'rishi/kuzatishi/kiritishi uchun API")
class UserAdminViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = IsAdminRole,

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return Response({
            "Jami": User.objects.count(),
            "Klientlar": User.objects.filter(role=User.Role.CLIENT).count(),
            "Ishchilar": User.objects.filter(role=User.Role.WORKER).count(),
            "Addminlar": User.objects.filter(role=User.Role.ADMIN).count(),
        })


@extend_schema(tags=['Notifications'], description="Xabarlar tarixini kuzatish uchun API")
class NotificationViewSet(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = IsAuthenticated,

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.CLIENT or user.role == user.Role.WORKER:
            return Notification.objects.filter(receiver=self.request.user).order_by("-created_at")
        return Notification.objects.order_by("-created_at")
