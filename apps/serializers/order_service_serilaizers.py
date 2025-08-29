from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ModelSerializer

from apps.models import Service, Order

User = get_user_model()


class ServiceSerializer(ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class OrderCreateSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = "id", "service", "worker", "description"

    def create(self, validated_data):
        user = self.context['request'].user
        service = validated_data['service']
        price = service.base_price
        order = Order.objects.create(client_id=user.pk, service_id=service.pk, price=price, **validated_data)

        # Send WS notification
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            f"service_{service.id}",
            {
                "type": "order.created",
                "order_id": order.id,
                "service_id": service.id,
                "price": str(order.price),
            }
        )
        return order


class OrderSerializer(ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    # def update(self, instance, validated_data):
    #     request = self.context["request"]
    #     if "status" in validated_data and request.user == instance.client:
    #         raise PermissionDenied("Mijoz buyurtma holatini o'zgartiraolmaydi!")
    #     return super().update(instance, validated_data)
