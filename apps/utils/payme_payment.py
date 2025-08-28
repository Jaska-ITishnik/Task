import base64
import binascii
import datetime
import logging
import time
from dataclasses import dataclass
from decimal import Decimal

from django.db import DatabaseError, transaction
from django.utils.timezone import datetime as dt
from django.utils.timezone import make_aware
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Transaction
from apps.serializers import MerchantTransactionsSerializer
from apps.utils.payme_exceptions import (MethodNotFound,
                                         PerformTransactionDoesNotExist,
                                         PermissionDenied, TooManyRequests)
from root.settings import PAYMENT

assert PAYMENT.get('PAYME')
assert PAYMENT['PAYME'].get('PAYME_ID')
assert PAYMENT['PAYME'].get('PAYME_KEY')
assert PAYMENT['PAYME'].get('PAYME_ACCOUNT')
assert PAYMENT['PAYME'].get('PAYME_CALL_BACK_URL')
assert PAYMENT['PAYME'].get('PAYME_URL')

PAYME = PAYMENT['PAYME']

PAYME_ID = PAYME['PAYME_ID']
PAYME_KEY = PAYME['PAYME_KEY']
PAYME_ACCOUNT = PAYME['PAYME_ACCOUNT']
PAYME_CALL_BACK_URL = PAYME['PAYME_CALL_BACK_URL']
PAYME_URL = PAYME["PAYME_URL"]

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class PaymeMerchantMethods:
    serializer = MerchantTransactionsSerializer

    def get_cleaned_data(self, params: dict):
        serializer = self.serializer(data=self.get_params(params))
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def make_aware_datetime(self, start_date: int, end_date: int):
        """
        Convert Unix timestamps to aware datetimes.

        :param start_date: Unix timestamp (milliseconds)
        :param end_date: Unix timestamp (milliseconds)

        :return: A tuple of two aware datetimes
        """
        return map(
            lambda timestamp: make_aware(
                dt.fromtimestamp(
                    timestamp / 1000
                )
            ),
            [start_date, end_date]
        )

    def get_params(self, params: dict) -> dict:
        """
        Use this function to get the parameters from the payme.
        """
        account: dict = params.get("account")

        clean_params: dict = {}
        clean_params["id"] = params.get("id")
        clean_params["time"] = params.get("time")
        clean_params["amount"] = params.get("amount")
        clean_params["reason"] = params.get("reason")

        # get statement method params
        clean_params["start_date"] = params.get("from")
        clean_params["end_date"] = params.get("to")

        if account is not None:
            account_name: str = PAYME_ACCOUNT
            clean_params["order_id"] = account[account_name]

        return clean_params


class CancelTransaction(PaymeMerchantMethods):
    """
    CancelTransaction class
    That is used to cancel a transaction.

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/metody-merchant-api/canceltransaction
    """

    @transaction.atomic
    def __call__(self, params: dict):
        clean_data: dict = self.get_cleaned_data(params)

        try:
            with transaction.atomic():
                _transaction: Transaction = Transaction.objects.get(payme_id=clean_data.get('id'))
                if _transaction.cancel_time == 0:
                    _transaction.cancel_time = int(time.time() * 1000)
                if _transaction.perform_time == 0:
                    _transaction.state = -1
                if _transaction.perform_time != 0:
                    _transaction.state = -2
                _transaction.reason = clean_data.get("reason")
                _transaction.status = Transaction.Status.CANCELED
                _transaction.save()

        except PerformTransactionDoesNotExist as error:
            logger.error("Paycom transaction does not exist: %s", error)
            raise PerformTransactionDoesNotExist() from error

        response: dict = {
            "result": {
                "state": _transaction.state,
                "cancel_time": _transaction.cancel_time,
                "transaction": str(_transaction.order_id),
                "reason": _transaction.reason,
            }
        }

        return _transaction.order_id, response


class CheckPerformTransaction(PaymeMerchantMethods):
    """
    CheckPerformTransaction class
    That's used to check perform transaction.

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/metody-merchant-api/checktransaction
    """

    def __call__(self, params: dict) -> tuple:
        response = {
            "result": {
                "allow": True,
            }
        }

        return None, response


class CheckTransaction(PaymeMerchantMethods):
    """
    CheckTransaction class
    That's used to check transaction

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/metody-merchant-api/checkperformtransaction
    """

    def __call__(self, params: dict) -> tuple:
        clean_data: dict = self.get_cleaned_data(params)

        try:
            _transaction = Transaction.objects.get(payme_id=clean_data.get("id"))
            response = {
                "result": {
                    "create_time": int(_transaction.created_at_ms),
                    "perform_time": _transaction.perform_time,
                    "cancel_time": _transaction.cancel_time,
                    "transaction": str(_transaction.order_id),
                    "state": _transaction.state,
                    "reason": _transaction.reason
                }
            }

        except Exception as error:
            logger.error("Error getting transaction in database: %s", error)
            print(error)

        return None, response


class CreateTransaction(PaymeMerchantMethods):
    """
    CreateTransaction class
    That's used to create transaction

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/metody-merchant-api/createtransaction
    """

    def __call__(self, params: dict) -> tuple:
        clean_data: dict = self.get_cleaned_data(params)

        order_id = clean_data.get("order_id")
        _transaction = Transaction.objects.get(order_id=order_id)
        if _transaction.created_at_ms is None:
            _transaction.created_at_ms = int(time.time() * 1000)
            _transaction.payme_id = clean_data.get('id')
            _transaction.save()
        try:
            if _transaction.payme_id != clean_data.get("id"):
                raise TooManyRequests()

        except TooManyRequests as error:
            logger.error("Too many requests for transaction %s", error)
            raise TooManyRequests() from error

        if _transaction:
            response: dict = {
                "result": {
                    "create_time": int(_transaction.created_at_ms),
                    "transaction": str(_transaction.order_id),
                    "state": _transaction.state,
                }
            }

        return order_id, response

    @staticmethod
    def _convert_ms_to_datetime(time_ms: int) -> datetime:
        return datetime.datetime.fromtimestamp(time_ms / 1000)


class GetStatement(PaymeMerchantMethods):
    """
    GetStatement class
    Transaction information is used for reconciliation
    of merchant and Payme Business transactions.

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/metody-merchant-api/getstatement
    """

    def __call__(self, params: dict) -> tuple:
        clean_data: dict = self.get_cleaned_data(params)

        start_date, end_date = int(clean_data.get("start_date")), int(clean_data.get("end_date"))

        try:
            _transactions = Transaction.objects.filter(created_at_ms__gte=start_date, created_at_ms__lte=end_date)

            if not _transactions:  # no transactions found for the period
                return None, {"result": {"transactions": []}}
            statements = [
                {
                    'id': _t.id,
                    'time': int(_t.created_at.timestamp()),
                    'amount': _t.amount,
                    'account': {'order_id': _t.order_id},
                    'create_time': int(_t.created_at_ms),
                    'perform_time': _t.perform_time,
                    'cancel_time': _t.cancel_time,
                    'transaction': _t.order_id,
                    'state': _t.state,
                    'reason': None,
                    'receivers': []  # not implemented
                } for _t in _transactions
            ]

            response: dict = {
                "result": {
                    "transactions": statements
                }
            }
        except DatabaseError as error:
            logger.error("Error getting transaction in database: %s", error)
            response = {"result": {"transactions": []}}

        return None, response


class PerformTransaction(PaymeMerchantMethods):
    """
    PerformTransaction class
    That's used to perform a transaction.

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/metody-merchant-api/performtransaction
    """

    def __call__(self, params: dict) -> tuple:
        clean_data: dict = self.get_cleaned_data(params)

        try:
            _transaction = Transaction.objects.get(payme_id=clean_data.get('id'))
            _transaction.state = 2
            if _transaction.perform_time == 0:
                _transaction.perform_time = int(time.time() * 1000)
            _transaction.status = Transaction.Status.CONFIRMED
            _transaction.change_status(Transaction.Status.CONFIRMED)
            _transaction.save()
            response: dict = {
                "result": {
                    "perform_time": int(_transaction.perform_time),
                    "transaction": str(_transaction.order_id),
                    "state": int(_transaction.state),
                }
            }
        except Exception as error:
            logger.error("error while getting transaction in db: %s", error)

        return _transaction.order_id, response


@dataclass
class GeneratePayLink:
    """
    GeneratePayLink dataclass
    That's used to generate pay lint for each order.

    Parameters
    ----------
    order_id: int — The order_id for paying
    amount: int — The amount belong to the order
    callback_url: str \
        The merchant api callback url to redirect after payment. Optional parameter.
        By default, it takes PAYME_CALL_BACK_URL from your settings

    Returns str — pay link
    ----------------------

    Full method documentation
    -------------------------
    https://developer.help.paycom.uz/initsializatsiya-platezhey/
    """
    order_id: str
    amount: Decimal
    callback_url: str = None

    @staticmethod
    def generate_url(order_id, amount, return_url=None) -> str:
        generated_pay_link: str = "{payme_url}/{encode_params}"
        params: str = 'm={payme_id};ac.{payme_account}={order_id};a={amount};c={call_back_url}'

        if return_url:
            redirect_url = return_url
        else:
            redirect_url = PAYME_CALL_BACK_URL

        params = params.format(
            payme_id=PAYME_ID,
            payme_account=PAYME_ACCOUNT,
            order_id=order_id,
            amount=amount,
            call_back_url=redirect_url
        )
        encode_params = base64.b64encode(params.encode("utf-8"))
        return generated_pay_link.format(payme_url=PAYME_URL, encode_params=str(encode_params, 'utf-8'))

    @staticmethod
    def to_tiyin(amount: Decimal) -> Decimal:
        return amount * 100

    @staticmethod
    def to_sum(amount: Decimal) -> Decimal:
        return amount / 100


class MerchantAPIView(APIView):
    """
    MerchantAPIView class provides payme call back functionality.
    """
    permission_classes = ()
    authentication_classes = ()

    def post(self, request) -> Response:
        """
        Payme sends post request to our call back url.
        That methods are includes 6 methods
            - CheckPerformTransaction
            - CreateTransaction
            - PerformTransaction
            - CancelTransaction
            - CheckTransaction
            - GetStatement
        """
        password = request.META.get('HTTP_AUTHORIZATION')
        if self.authorize(password):
            incoming_data: dict = request.data
            incoming_method: str = incoming_data.get("method")

            logger.info("Call back data is incoming %s", incoming_data)

            try:
                paycom_method = self.get_paycom_method_by_name(incoming_method=incoming_method)
            except ValidationError as error:
                logger.error("Validation Error occurred: %s", error)
                raise MethodNotFound() from error

            except PerformTransactionDoesNotExist as error:
                logger.error("PerformTransactionDoesNotExist Error occurred: %s", error)
                raise PerformTransactionDoesNotExist() from error

            order_id, action = paycom_method(incoming_data.get("params"))

        if isinstance(paycom_method, CreateTransaction):
            self.create_transaction(order_id, action)

        if isinstance(paycom_method, PerformTransaction):
            self.perform_transaction(order_id, action)

        if isinstance(paycom_method, CancelTransaction):
            self.cancel_transaction(order_id, action)

        return Response(action)

    def get_paycom_method_by_name(self, incoming_method: str) -> object:
        """
        Use this static method to get the paycom method by name.
        :param incoming_method: string -> incoming method name
        """
        available_methods: dict = {
            "CheckPerformTransaction": CheckPerformTransaction,
            "CreateTransaction": CreateTransaction,
            "PerformTransaction": PerformTransaction,
            "CancelTransaction": CancelTransaction,
            "CheckTransaction": CheckTransaction,
            "GetStatement": GetStatement
        }

        try:
            merchant_method = available_methods[incoming_method]
        except Exception as error:
            error_message = "Unavailable method: %s", incoming_method
            logger.error(error_message)
            raise MethodNotFound(error_message) from error

        merchant_method = merchant_method()

        return merchant_method

    @staticmethod
    def authorize(password: str) -> bool:
        """
        Authorize the Merchant.
        :param password: string -> Merchant authorization password
        """
        is_payme: bool = False
        error_message: str = ""

        if not isinstance(password, str):
            error_message = "Request from an unauthorized source!"
            logger.error(error_message)
            raise PermissionDenied(error_message)

        password = password.split()[-1]

        try:
            password = base64.b64decode(password).decode('utf-8')
        except (binascii.Error, UnicodeDecodeError) as error:
            error_message = "Error when authorize request to merchant!"
            logger.error(error_message)

            raise PermissionDenied(error_message) from error

        merchant_key = password.split(':')[-1]

        if merchant_key == PAYME_KEY:
            is_payme = True

        if merchant_key != PAYME_KEY:
            logger.error("Invalid key in request!")

        if is_payme is False:
            raise PermissionDenied("Unavailable data for unauthorized users!")

        return is_payme

    def create_transaction(self, order_id, action) -> None:
        """
        need implement in your view class
        """
        pass

    def perform_transaction(self, order_id, action) -> None:
        """
        need implement in your view class
        """
        pass

    def cancel_transaction(self, order_id, action) -> None:
        """
        need implement in your view class
        """
        pass
