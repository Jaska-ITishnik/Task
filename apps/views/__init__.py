from apps.views.auth import orders_dashboard, LoginAPIView, RegisterView
from apps.views.order_services import ServiceViewSet, OrderViewSet
from apps.views.payment import TransactionCreateAPIView, TransactionClickCheckAPIView, TransactionPaymeCheckAPIView, \
    TransactionListAPIVew, TransactionRetrieveAPIView, ClickQRAPIView
