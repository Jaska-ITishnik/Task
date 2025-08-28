from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.models import Service, Order, Notification
from apps.serializers import ServiceSerializer, OrderCreateSerializer, OrderSerializer

User = get_user_model()


@extend_schema(tags=['Services'], description="Servislarni boshqarish uchun API")
class ServiceViewSet(ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


@extend_schema(tags=['Orders'], description="Buyurtmalarni boshqarish uchun API")
class OrderViewSet(ModelViewSet):
    queryset = Order.objects.select_related('service', 'client', 'worker')

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.ADMIN:
            return self.queryset
        if user.role == user.Role.CLIENT:
            return self.queryset.filter(client=user)
        if user.role == user.Role.WORKER:
            return self.queryset.filter(Q(worker=user) | Q(service__name__icontains=user.specialty))
        return Order.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        old_order = self.get_object()
        old_status = old_order.status

        order = serializer.save()
        new_status = order.status

        if new_status in [Order.Status.IN_PROCESS, Order.Status.COMPLETED]:
            if user.role not in [user.Role.WORKER, user.Role.ADMIN]:
                raise PermissionDenied("Sizda bu statusni o‘zgartirish huquqi yo‘q!")

        if old_status != new_status:
            channel_layer = get_channel_layer()

            receiver = order.client
            sender = user

            notification = Notification.objects.create(
                sender=sender,
                receiver=receiver,
                message=f"Buyurtma holati {new_status} ga o‘zgardi."
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{receiver.id}",
                {
                    "type": "send_message",
                    "message": notification.message,
                }
            )
