from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     RetrieveAPIView, get_object_or_404)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Transaction
from apps.serializers import (ClickSerializer, ClickTransactionSerializer,
                              TransactionDetailModelSerializer,
                              TransactionListModelSerializer)
from apps.utils.click_payment import (AUTHORIZATION_FAIL,
                                      AUTHORIZATION_FAIL_CODE, COMPLETE,
                                      PREPARE, ClickShopAPIView, click_get_qr_url)
from apps.utils.payme_payment import GeneratePayLink, MerchantAPIView


@extend_schema(tags=['payment'],
               responses={200: {'type': 'object',
                                'properties': {'url': {'type': 'string'}, }}})
class TransactionCreateAPIView(CreateAPIView):
    serializer_class = ClickSerializer
    permission_classes = IsAuthenticated,

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.data.get('amount')
        return_url = serializer.data.get('return_url')
        _type = serializer.data.get('type')
        order_id = serializer.data.get('order_id')
        _name = serializer.data.get('name')

        transaction, _ = Transaction.objects.get_or_create(
            amount=amount, order_id=order_id, payment_type=_type, user=self.request.user, name=_name
        )
        if _type == Transaction.PaymentType.CLICK:
            url = ClickShopAPIView.generate_url(transaction.order_id, amount, return_url=return_url)
        elif _type == Transaction.PaymentType.PAYME:
            url = GeneratePayLink.generate_url(transaction.order_id, amount * 100, return_url=return_url)
        else:
            raise ValidationError({"message": "Bunday to'lov tizimi yoq"})

        response = {
            'payment_link': url
        }
        return Response(response)


@extend_schema(tags=['payment'])
class TransactionClickCheckAPIView(ClickShopAPIView):
    serializer_class = ClickTransactionSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        METHODS = {
            PREPARE: self.prepare,
            COMPLETE: self.complete
        }

        merchant_trans_id = serializer.validated_data['merchant_trans_id']
        amount = serializer.validated_data['amount']
        action = serializer.validated_data['action']
        if self.authorization(**serializer.validated_data) is False:
            return Response({
                "error": AUTHORIZATION_FAIL_CODE,
                "error_note": AUTHORIZATION_FAIL
            })

        check_order = self.check_order(merchant_trans_id, amount)
        if check_order is True:
            result = METHODS[action](**serializer.validated_data)
            return Response(result)
        return Response({"error": check_order})


@extend_schema(tags=['payment'])
class TransactionPaymeCheckAPIView(MerchantAPIView):
    def create_transaction(self, order_id, action, *args, **kwargs) -> None:
        print(f"CCCCCC create_transaction for order_id: {order_id}, response: {action}")

    def perform_transaction(self, order_id, action, *args, **kwargs) -> None:
        print(f"PPPPPP perform_transaction for order_id: {order_id}, response: {action}")

    def cancel_transaction(self, order_id, action, *args, **kwargs) -> None:
        print(f"CANNN cancel_transaction for order_id: {order_id}, response: {action}")


@extend_schema(tags=['payment'])
class TransactionListAPIVew(ListAPIView):
    queryset = Transaction.objects.all().order_by('-created_at')
    serializer_class = TransactionListModelSerializer
    permission_classes = IsAuthenticated,

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user, status=Transaction.Status.CONFIRMED)


@extend_schema(tags=['payment'])
class TransactionRetrieveAPIView(RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionDetailModelSerializer
    permission_classes = IsAuthenticated,
    lookup_field = 'order_id'

    def get_object(self):
        order_id = self.kwargs.get(self.lookup_field)
        return get_object_or_404(self.queryset, order_id=order_id)


@extend_schema(tags=['payment'])
class ClickQRAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    """
    Harid chekni olish uchun api
    """

    def post(self, request, *args, **kwargs):
        transaction_id = kwargs["transaction_id"]
        tx = get_object_or_404(Transaction, id=transaction_id, user=request.user, status=Transaction.Status.CONFIRMED)
        if not tx.payment_id:
            return Response({
                "detail": "Tulov muaffaqiyatli amalga oshirilmagan !!!"},
                status=status.HTTP_409_CONFLICT)

        qr_url = click_get_qr_url(int(tx.payment_id))
        if not qr_url:
            return Response({"detail": "QR URL topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"qr_url": qr_url}, status=status.HTTP_200_OK)
