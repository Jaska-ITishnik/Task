from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from apps.models import User, Order, Service, Notification, Transaction


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("role", "phone", "specialty")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "password1", "password2"),
            },
        ),
    )


@admin.register(Order)
class OrderModelAdmin(ModelAdmin):
    list_display = 'client', 'worker', 'service', 'price', 'status'


@admin.register(Service)
class ServiceModelAdmin(ModelAdmin):
    list_display = "id", "name", "base_price"


@admin.register(Notification)
class NotificationModelAdmin(ModelAdmin):
    list_display = 'sender', 'receiver', 'message', 'is_read', 'created_at'


@admin.register(Transaction)
class TransactionModelAdmin(admin.ModelAdmin):
    list_display = 'status', 'payment_type', 'amount'
