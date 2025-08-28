from rest_framework.exceptions import ValidationError
from rest_framework.fields import URLField
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import (CharField, ChoiceField, IntegerField,
                                        ModelSerializer, Serializer)

from apps.models import Transaction, Order
from apps.utils.payme_exceptions import IncorrectAmount, PerformTransactionDoesNotExist


class ClickSerializer(Serializer):
    amount = IntegerField(help_text="To'lov summasi", max_value=1_000_000_000, default=1000, required=False)
    return_url = URLField(help_text="To'lovdan so'ng qaytadigan url", required=False)
    type = ChoiceField(choices=Transaction.PaymentType.choices)
    order_id = IntegerField(help_text='Buyurtma raqami', required=True)
    name = CharField()

    def validate(self, attrs):
        obj = get_object_or_404(Order, id=attrs['order_id'])
        exact_price = obj.price
        if attrs['amount'] != exact_price:
            attrs['amount'] = exact_price
        if transaction := Transaction.objects.filter(order=attrs['order_id']).first():
            if transaction.status == transaction.Status.CONFIRMED:
                raise ValidationError('Bu orderga uchun to\'lov tasdiqlangan')
            else:
                transaction.delete()
        return attrs


class ClickTransactionSerializer(Serializer):
    click_trans_id = CharField(allow_blank=True)
    service_id = CharField(allow_blank=True)
    merchant_trans_id = CharField(allow_blank=True)
    merchant_prepare_id = CharField(allow_blank=True, required=False, allow_null=True)
    amount = CharField(allow_blank=True)
    action = CharField(allow_blank=True)
    error = CharField(allow_blank=True)
    error_note = CharField(allow_blank=True)
    sign_time = CharField()
    sign_string = CharField(allow_blank=True)
    click_paydoc_id = CharField(allow_blank=True)


class TransactionListModelSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = 'id', 'payment_type', 'name', 'created_at', 'status', 'amount', 'order'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['order_id'] = instance.order.app_id
        return rep


class MerchantTransactionsSerializer(Serializer):
    id = CharField(allow_null=True, required=False)
    start_date = IntegerField(allow_null=True, required=False)
    end_date = IntegerField(allow_null=True, required=False)
    order_id = CharField(allow_null=True, required=False)
    amount = IntegerField(allow_null=True, required=False)
    reason = IntegerField(allow_null=True, required=False)

    def validate(self, attrs) -> dict:
        """
        Validate the data given to the MerchantTransactionsModel.
        """
        if attrs.get("order_id") is not None:
            try:
                transaction = Transaction.objects.get(order_id=attrs['order_id'])
                if transaction.amount * 100 != int(attrs['amount']):
                    raise IncorrectAmount()

            except IncorrectAmount as error:
                raise IncorrectAmount() from error

        return attrs

    def validate_order_id(self, order_id) -> int:
        try:
            Transaction.objects.get(order_id=order_id)
        except Transaction.DoesNotExist as error:
            raise PerformTransactionDoesNotExist() from error

        return order_id


class TransactionDetailModelSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = 'id', 'name', 'amount', 'payment_type', 'status'
