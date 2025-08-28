from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.conf import settings
from django.db import close_old_connections
from jwt import InvalidSignatureError, ExpiredSignatureError, DecodeError
from jwt import decode as jwt_decode


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser  # ✅ lazy import
        close_old_connections()
        query_params = parse_qs(scope["query_string"].decode("utf8"))
        token = query_params.get("token", [None])[0]

        if not token:
            scope["user"] = AnonymousUser()
            return await self.app(scope, receive, send)

        try:
            data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = data.get("user_id") or data.get("id") or data.get("sub")
            scope["user"] = await self.get_user(user_id)
        except (InvalidSignatureError, ExpiredSignatureError, DecodeError, KeyError, TypeError) as e:
            print("JWT decode error:", e)
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth.models import AnonymousUser  # ✅ lazy import
        from django.contrib.auth import get_user_model  # ✅ lazy import
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()


def JWTAuthMiddlewareStack(app):
    return JWTAuthMiddleware(AuthMiddlewareStack(app))
