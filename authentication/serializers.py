from rest_framework import serializers
from .models import User
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from .models import User
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password"]

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        email = validated_data.get("email", "")
        filtered_user_by_email = User.objects.filter(email=email)

        if filtered_user_by_email.exists():
            raise AuthenticationFailed("Email already exists, try again")

        password = validated_data.get("password", "")
        try:
            validate_password(password)
        except Exception:
            raise serializers.ValidationError(
                {"password": "Password is not strong enough."}
            )

        return validated_data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(write_only=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "tokens",
            "email_verified",
            "profile_completed",
        ]
        read_only_fields = [
            "email_verified",
            "profile_completed",
        ]

    def get_tokens(self, obj):
        user = User.objects.get(email=obj["email"])

        return {"refresh": user.tokens()["refresh"], "access": user.tokens()["access"]}

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get("email", "")
        password = validated_data.get("password", "")
        user = auth.authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials, try again")
        if not user.is_active:
            raise AuthenticationFailed("Account disabled, contact admin")

        self.context["user"] = user
        return validated_data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get("user")
        if user:
            data["email_verified"] = user.email_verified
            data["profile_completed"] = user.profile_completed
            data["current_subscription"] = user.current_subscription
        return data


class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ["token"]


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ["email"]


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ["password", "token", "uidb64"]

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        try:
            password = validated_data.get("password")
            token = validated_data.get("token")
            uidb64 = validated_data.get("uidb64")

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("The reset link is invalid", 401)

            user.set_password(password)
            user.save()

            return user
        except Exception as e:
            raise AuthenticationFailed("The reset link is invalid", 401)


class ChangPasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    re_new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.context.get("user")
        validated_data = super().validate(attrs)
        old_password = validated_data.get("old_password")
        new_password = validated_data.get("new_password")
        re_new_password = validated_data.get("re_new_password")

        # check if old password is valid
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Invalid password"})

        # check if passwords match
        if new_password != re_new_password:
            raise serializers.ValidationError(
                {"password": "Password fields do not match"}
            )
        try:
            validate_password(new_password)
        except Exception:
            raise serializers.ValidationError(
                {"new_password": "Password is not strong enough."}
            )

        return validated_data


class logoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RequestVerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ["email"]


class RequestRestPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ["email"]
