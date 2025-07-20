from rest_framework import serializers
from .models import User, PasswordReset
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError("User with this Email already exists.")
        return value

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=self.context.get('phone_number'),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class PasswordResetConfirmSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = PasswordReset
        fields = ['email', 'otp', 'password']

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')

        # Check if user exists
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")

        # Ensure the OTP is valid and not expired
        password_reset = PasswordReset.objects.filter(user=user, otp=otp, is_used=False).first()
        if not password_reset:
            raise serializers.ValidationError("Invalid or expired OTP.")

        if password_reset.expires_at < timezone.now():
            raise serializers.ValidationError("OTP has expired.")

        # Store user and password_reset object for later use in save method
        data['user'] = user
        data['password_reset'] = password_reset

        return data

    def save(self, **kwargs):
        user = self.validated_data['user'] # type: ignore
        password_reset = self.validated_data['password_reset'] # type: ignore
        new_password = self.validated_data['password'] # type: ignore

        # Set the new password for the user
        user.set_password(new_password)
        user.save()

        # Mark the OTP as used
        password_reset.is_used = True
        password_reset.save()

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.CharField(source='payment_status')
    member_since = serializers.DateTimeField(source='created_at', format='%Y-%m-%d')

    class Meta:
        model = User
        fields = [
            'full_name',
            'email',
            'company',
            'location',
            'phone_number',
            'website',
            'subscription_plan',
            'member_since'
        ]
