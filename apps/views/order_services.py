from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from apps.models import Service, Order
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

    def destroy(self, request, *args, **kwargs):
        if request.user.role == 'client':
            raise PermissionDenied("Mijoz buyurtmani o'chiraolmaydi!")
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.role == "client":
            raise PermissionDenied("Mijoz buyurtma holatini o'zgartiraolmaydi!")
        return super().update(request, *args, **kwargs)
