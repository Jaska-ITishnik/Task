from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.views import RegisterView, LoginAPIView, ServiceViewSet, OrderViewSet, \
    orders_dashboard, TransactionCreateAPIView, TransactionClickCheckAPIView, \
    TransactionPaymeCheckAPIView, TransactionListAPIVew, TransactionRetrieveAPIView, ClickQRAPIView
from apps.views.users import UserAdminViewSet, NotificationViewSet, MeView

router = DefaultRouter()
router.register(r'users', UserAdminViewSet, basename='users-admin')
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [

    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # notifications
    path('notifications/', NotificationViewSet.as_view(), name='notifications'),
    path('notification-page/', orders_dashboard, name='notification_page'),

    # Profile
    path('me/', MeView.as_view(), name='me'),

    # Admin user management
    path('admin/', include(router.urls)),

    # Payment
    path('payment', TransactionCreateAPIView.as_view(), name='payment'),
    path('payment/click', TransactionClickCheckAPIView.as_view(), name='payment_click_check'),
    path('payment/payme', TransactionPaymeCheckAPIView.as_view(), name='payment_payme_check'),
    path('payment/transactions', TransactionListAPIVew.as_view(), name='transactions'),
    path('payment/check-order/<int:order_id>', TransactionRetrieveAPIView.as_view(), name='check_order'),
    path('payment/qr-code/<int:transaction_id>', ClickQRAPIView.as_view(), name='qr_code'),

]
