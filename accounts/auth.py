from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=False)
    username = serializers.CharField(required=False, allow_blank=False)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        username = attrs.get("username")
        password = attrs["password"]

        if email and username:
            raise serializers.ValidationError("Use either email or username, not both.")

        request = self.context.get("request")

        if username:
            admin_user = (
                User.objects.filter(username=username, is_staff=True)
                .order_by("-is_superuser", "id")
                .first()
            )
            if not admin_user:
                raise serializers.ValidationError({"detail": "Invalid admin credentials."})
            user = authenticate(request=request, username=admin_user.email, password=password)
            if not user or not user.is_staff:
                raise serializers.ValidationError({"detail": "Invalid admin credentials."})
            attrs["user"] = user
            return attrs

        if not email:
            raise serializers.ValidationError({"email": ["This field is required."]})

        user = authenticate(request=request, username=email, password=password)
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is disabled."})
        attrs["user"] = user
        return attrs


class EmailTokenObtainPairView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "is_admin": user.is_staff,
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )
