from django.contrib.auth import get_user_model, login
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework_simplejwt.tokens import RefreshToken

from apps.serializers.user_serializers import RegisterSerializer, LoginSerializer

User = get_user_model()


@extend_schema(tags=['Auth'], description="Userlar royxatdan o'tish uchun API")
class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = AllowAny,


@extend_schema(tags=['Auth'], description="Userlar login uchun API")
class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = AllowAny,

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        tokens = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(tokens.access_token),
                "refresh": str(tokens)
            },
            status=HTTP_200_OK
        )


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def orders_dashboard(request):
    tokens = get_tokens_for_user(request.user)
    user_role = request.user.role
    ctx = {
        "user_type": user_role,
        "token": tokens["access"]
    }

    return render(request, "orders_dashboard.html", ctx)
