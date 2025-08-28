import datetime
import hashlib
import time

import requests
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.models import Transaction
from root.settings import PAYMENT

assert PAYMENT.get('CLICK')
assert PAYMENT['CLICK'].get('CLICK_MERCHANT_ID')
assert PAYMENT['CLICK'].get('CLICK_MERCHANT_USER_ID')
assert PAYMENT['CLICK'].get('CLICK_SECRET_KEY')
assert PAYMENT['CLICK'].get('CLICK_SERVICE_ID')

CLICK = PAYMENT['CLICK']

CLICK_MERCHANT_ID = CLICK['CLICK_MERCHANT_ID']
CLICK_MERCHANT_USER_ID = CLICK['CLICK_MERCHANT_USER_ID']
CLICK_SECRET_KEY = CLICK['CLICK_SECRET_KEY']
CLICK_SERVICE_ID = CLICK['CLICK_SERVICE_ID']
CLICK_API = CLICK['CLICK_API']

INVALID_AMOUNT = '-2'
INVALID_ACTION = -4
TRANSACTION_NOT_FOUND = '-6'
ORDER_NOT_FOUND = '-5'
PREPARE = '0'
COMPLETE = '1'
A_LACK_OF_MONEY = '-5017'
A_LACK_OF_MONEY_CODE = -9
AUTHORIZATION_FAIL = 'AUTHORIZATION_FAIL'
AUTHORIZATION_FAIL_CODE = '-1'
ORDER_FOUND = True
SUCCESS = 0
TRANSACTION_CANCELLED = '-9'
ALREADY_PAID = '-4'
ACTION_NOT_FOUND = '-3'


class ClickShopAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def authorization(self, click_trans_id: str, amount: int, action: str, sign_time: datetime.datetime,
                      sign_string: str,
                      merchant_trans_id: str, merchant_prepare_id: str = None, *args, **kwargs) -> bool:
        text = f"{click_trans_id}{CLICK_SERVICE_ID}{CLICK_SECRET_KEY}{merchant_trans_id}"
        if merchant_prepare_id != "" and merchant_prepare_id is not None:
            text += f"{merchant_prepare_id}"
        text += f"{amount}{action}{sign_time}"
        encoded_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if encoded_hash != sign_string:
            return False
        return True

    @classmethod
    def order_load(cls, order_id):
        if int(order_id) > 1000000000:
            return None
        return get_object_or_404(Transaction, order_id=order_id)

    @classmethod
    def click_webhook_errors(cls, click_trans_id: str,
                             service_id: str,
                             click_paydoc_id: str,
                             merchant_trans_id: str,
                             amount: str,
                             action: str,
                             sign_time: str,
                             sign_string: str,
                             error: str,
                             merchant_prepare_id: str = None) -> dict:

        merchant_prepare_id = merchant_prepare_id if action and action == '1' else ''
        created_sign_string = '{}{}{}{}{}{}{}{}'.format(click_trans_id, service_id, CLICK_SECRET_KEY, merchant_trans_id,
                                                        merchant_prepare_id, amount, action, sign_time)
        encoder = hashlib.md5(created_sign_string.encode('utf-8'))
        created_sign_string = encoder.hexdigest()
        if created_sign_string != sign_string:
            return {
                'error': AUTHORIZATION_FAIL_CODE,
                'error_note': _('SIGN CHECK FAILED!')
            }

        if action not in [PREPARE, COMPLETE]:
            return {
                'error': ACTION_NOT_FOUND,
                'error_note': _('Action not found')
            }

        order = cls.order_load(merchant_trans_id)
        if not order:
            return {
                'error': ORDER_NOT_FOUND,
                'error_note': _('Order not found')
            }

        if abs(float(amount) - float(order.amount) > 0.01):
            return {
                'error': INVALID_AMOUNT,
                'error_note': _('Incorrect parameter amount')
            }

        if order.status == Transaction.Status.CONFIRMED:
            return {
                'error': ALREADY_PAID,
                'error_note': _('Already paid')
            }

        if action == COMPLETE:
            if merchant_trans_id != merchant_prepare_id:
                return {
                    'error': TRANSACTION_NOT_FOUND,
                    'error_note': _('Transaction not found')
                }

        if order.status == Transaction.Status.CANCELED or int(error) < 0:
            return {
                'error': TRANSACTION_CANCELLED,
                'error_note': _('Transaction cancelled')
            }
        return {
            'error': SUCCESS,
            'error_note': 'Success'
        }

    @classmethod
    def prepare(cls, click_trans_id: str,
                service_id: str,
                click_paydoc_id: str,
                merchant_trans_id: str,
                amount: str,
                action: int,
                sign_time: str,
                sign_string: str,
                error: str,
                error_note: str,
                *args, **kwargs) -> dict:
        result = cls.click_webhook_errors(click_trans_id, service_id, click_paydoc_id, merchant_trans_id,
                                          amount, action, sign_time, sign_string, error)
        transaction = cls.order_load(merchant_trans_id)
        if result['error'] == '0':
            transaction.change_status(Transaction.Status.PROCESSING)
        result['click_trans_id'] = click_trans_id
        result['merchant_trans_id'] = merchant_trans_id
        result['merchant_prepare_id'] = merchant_trans_id
        result['merchant_confirm_id'] = merchant_trans_id
        return result

    @classmethod
    def complete(cls, click_trans_id: str,
                 service_id: str,
                 click_paydoc_id: str,
                 merchant_trans_id: str,
                 amount: str,
                 action: str,
                 sign_time: str,
                 sign_string: str,
                 error: str,
                 error_note: str,
                 merchant_prepare_id: str = None,
                 *args, **kwargs) -> dict:
        transaction = cls.order_load(merchant_trans_id)
        result = cls.click_webhook_errors(click_trans_id, service_id, click_paydoc_id, merchant_trans_id,
                                          amount, action, sign_time, sign_string, error, merchant_prepare_id)
        if error and int(error) < 0:
            transaction.change_status(Transaction.Status.CANCELED)
        if result['error'] == SUCCESS:
            transaction.change_status(Transaction.Status.CONFIRMED)
            cls.successfully_payment(transaction)
            transaction.payment_id = click_paydoc_id
            transaction.save()
        result['click_trans_id'] = click_trans_id
        result['merchant_trans_id'] = merchant_trans_id
        result['merchant_prepare_id'] = merchant_prepare_id
        result['merchant_confirm_id'] = merchant_prepare_id
        return result

    @staticmethod
    def generate_url(order_id, amount, return_url=None) -> str:
        url = f"https://my.click.uz/services/pay?service_id={CLICK_SERVICE_ID}&merchant_id={CLICK_MERCHANT_ID}&amount={amount}&transaction_param={order_id}"
        if return_url:
            url += f"&return_url={return_url}"
        return url

    @classmethod
    def check_order(cls, order_id: str, amount: str):
        if order_id:
            try:
                transaction = Transaction.objects.get(order_id=order_id)
                if int(amount) == transaction.amount:
                    return ORDER_FOUND
                else:
                    return INVALID_AMOUNT
            except Transaction.DoesNotExist:
                return ORDER_NOT_FOUND

    @classmethod
    def successfully_payment(cls, transaction: Transaction):
        """ Эта функция вызывается после успешной оплаты """
        transaction.change_status(Transaction.Status.CONFIRMED)


def click_get_qr_url(payment_id: int) -> str | None:
    ts = str(int(time.time()))
    digest = hashlib.sha1((ts + CLICK_SECRET_KEY).encode()).hexdigest()
    headers = {
        "Auth": f"{CLICK_MERCHANT_USER_ID}:{digest}:{ts}",
        "Accept": "application/json"
    }
    url = f"https://api.click.uz/v2/merchant/payment/ofd_data/{CLICK_SERVICE_ID}/{payment_id}"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json().get("qrCodeURL")
