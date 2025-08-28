from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.models import Order, Notification

_old_status = {}


@receiver(pre_save, sender=Order)
def cache_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            _old_status[instance.pk] = old.status
        except Order.DoesNotExist:
            _old_status[instance.pk] = None


@receiver(post_save, sender=Order)
def order_created_or_updated(sender, instance, created, **kwargs):
    worker = instance.worker
    client = instance.client
    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Error: Channel layer is None")
    else:
        print(f"Channel layer: {channel_layer}")

    if created:
        message = f"Yangi buyurtma: {instance.id}"
        Notification.objects.create(sender_id=client.id, receiver_id=worker.id, message=message)

        async_to_sync(channel_layer.group_send)(
            f"user_{worker.id}",
            {"type": "send_message", "message": message}
        )

        async_to_sync(channel_layer.group_send)(
            "admin_group",
            {"type": "send_message", "message": f"[ADMIN LOG] {message}"}
        )

    else:
        old_status = _old_status.get(instance.pk)
        new_status = instance.status
        msg = None

        if old_status != new_status:
            if new_status == "in_process":
                msg = f"Sizning buyurtmangiz qabul qilindi: {instance.id}"
            elif new_status == "completed":
                msg = f"Sizning buyurtmangiz ({instance.id}) yakunlandi ✅."
            elif new_status == "canceled":
                msg = f"Sizning buyurtmangiz ({instance.id}) bekor qilindi ❌."

            if msg:
                Notification.objects.create(sender_id=worker.id, receiver_id=client.id, message=msg)
                async_to_sync(channel_layer.group_send)(
                    f"user_{client.id}",
                    {"type": "send_message", "message": msg}
                )

                async_to_sync(channel_layer.group_send)(
                    "admin_group",
                    {"type": "send_message", "message": f"[ADMIN LOG] {msg}"}
                )

        if instance.pk in _old_status:
            del _old_status[instance.pk]
