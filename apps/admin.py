from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from apps.models import User, Order, Service, Notification, Transaction


@admin.register(User)
class UserAdmin(UserAdmin):
    pass


@admin.register(Order)
class OrderModelAdmin(ModelAdmin):
    pass


@admin.register(Service)
class ServiceModelAdmin(ModelAdmin):
    list_display = "id", "name"


@admin.register(Notification)
class NotificationModelAdmin(ModelAdmin):
    pass


@admin.register(Transaction)
class TransactionModelAdmin(admin.ModelAdmin):
    pass
