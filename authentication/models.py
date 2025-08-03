from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from decimal import Decimal

# Create your models here.

PAYMENT_STATUS_CHOICES = [
    ('free', 'Free'),
    ('pro', 'Pro'),
]


class UserManager(BaseUserManager):
    def create_user(self, email, user_name, password=None, **extra_fields):
        '''Creates and saves a User with the given email and password.

        :param email: The email address of the user
        :param user_name: The username of the user
        :param password: The password of the user
        :param extra_fields: Any extra fields to set on the user
        :return: The user object created by this function
        :raises ValueError: If the email address is not set
        '''
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, user_name, password=None, **extra_fields):
        """Create and save a superuser with the given email and password.

        It is imperative that the is_staff and is_superuser flags are set to
        True, as they are checked by the auth backend and the admin.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, user_name, password, **extra_fields)
    
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class User(AbstractBaseUser):
    username = models.CharField(max_length=255)
    auth_id = models.CharField(max_length=255, default="True")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    country = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    postal_code = models.CharField(max_length=50, null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    image = models.URLField(max_length=500, blank=True, null=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    account_type = models.CharField(max_length=50, default='user')
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(null=True, blank=True)
    
    is_paid = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='free')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal(0.00))

    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=255, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
    
    def soft_delete(self, admin_email):
        """Soft delete the user."""
        self.is_active = False
        self.deleted_at = now()
        self.deleted_by = admin_email
        self.save()


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'email_verification'


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'password_reset'
