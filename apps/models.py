from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, Model, TextField, DecimalField, ForeignKey, CASCADE, SET_NULL, PROTECT, \
    DateTimeField, BooleanField, OneToOneField
from django.db.models.enums import TextChoices
from django.db.models.fields import IntegerField, BigIntegerField
from django.db.models.functions import Now


class TimeBasedModel(Model):
    updated_at = DateTimeField(verbose_name='Yangilangan sana', auto_now=True)
    created_at = DateTimeField(verbose_name='Yaratilgan sana', auto_now_add=True, db_default=Now())

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(TextChoices):
        CLIENT = 'client', 'Client'
        WORKER = 'worker', 'Worker'
        ADMIN = 'admin', 'Admin'

    role = CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    phone = CharField(max_length=20, blank=True, null=True)
    specialty = CharField(max_length=100, blank=True, null=True)

    def is_admin(self):
        return self.role == User.Role.ADMIN or self.is_staff


class Service(TimeBasedModel):
    name = CharField(max_length=200)
    description = TextField(blank=True)
    base_price = DecimalField(max_digits=10, decimal_places=2)


class Order(TimeBasedModel):
    class Status(TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        IN_PROCESS = "in_process", "In_process"
        COMPLETED = "completed", "Completed"
        CANCELED = "canceled", "Canceled"

    client = ForeignKey('apps.User', related_name="orders", on_delete=CASCADE,
                        limit_choices_to={"role": User.Role.CLIENT})
    worker = ForeignKey('apps.User', null=True, blank=True, related_name="assigned_orders",
                        on_delete=SET_NULL, limit_choices_to={"role": User.Role.WORKER})
    service = ForeignKey('apps.Service', on_delete=PROTECT)
    price = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = TextField(blank=True)


class Notification(Model):
    sender = ForeignKey('apps.User', on_delete=CASCADE, related_name='sent_notifications', null=True, blank=True)
    receiver = ForeignKey('apps.User', on_delete=CASCADE, related_name='received_notifications')
    message = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender} to {self.receiver}: {self.message[:30]}"


class Transaction(TimeBasedModel):
    class Status(TextChoices):
        WAITING = 'waiting', "Kutilmoqda"
        PROCESSING = 'processing', "Jarayonda"
        CONFIRMED = 'confirmed', "To'landi"
        CANCELED = 'canceled', 'Bekor qilindi'

    class PaymentType(TextChoices):
        CLICK = 'click', 'Click'
        PAYME = 'payme', 'Payme'

    name = CharField(verbose_name="To'lov haqida", max_length=255, null=True, blank=True)
    status = CharField(verbose_name='Holati', max_length=25, choices=Status.choices, default=Status.WAITING)
    payment_type = CharField(verbose_name="To'lov turi", max_length=50, choices=PaymentType.choices)
    amount = IntegerField(verbose_name='Summasi')
    # created_at_ms, perform_time, cancel_time, state, reason, payme_id payme uchun kerakli fieldlar
    created_at_ms = BigIntegerField(null=True, blank=True, verbose_name="Created At MS")
    perform_time = BigIntegerField(null=True, default=0, verbose_name="Perform Time")
    cancel_time = BigIntegerField(null=True, default=0, verbose_name="Cancel Time")
    state = IntegerField(null=True, default=1, verbose_name="State")
    payme_id = CharField(max_length=255, null=True, blank=True)
    reason = IntegerField(null=True, blank=True)
    user = ForeignKey('apps.User', CASCADE)
    order = OneToOneField('apps.Order', CASCADE)
    payment_id = CharField("Payment Id", max_length=255, null=True, blank=True)

    def __str__(self):
        return f"transaction id {self.pk}"

    def change_status(self, status):
        order = self.order
        if self.status == Transaction.Status.CONFIRMED:
            order.status = self.order.Status.PAID
            order.save()
        elif self.status == Transaction.Status.CANCELED:
            order.status = self.order.Status.CANCELED
            order.save()
        self.status = status
        self.save()
