# shop/models.py
import random, string
from django.utils import timezone
from .constants import KVANTUM_CHOICES  # Импортируем KVANTUM_CHOICES
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class User(AbstractUser):
    is_kvantum_admin = models.BooleanField(
        default=False,
        verbose_name="Администратор квантума"
    )
    admin_kvantum = models.CharField(
        max_length=10,
        choices=KVANTUM_CHOICES,
        blank=True,
        null=True,
        verbose_name="Ответственный квантум"
    )

    # Важно: добавляем related_name для избежания конфликтов
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="custom_user_groups",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="custom_user",
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'auth_user'  # Это сохранит совместимость с ожиданиями Django

    def __str__(self):
        return self.username

class Achievement(models.Model):
    user = models.ForeignKey('shop.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, verbose_name="Название грамоты")
    file = models.FileField(upload_to='achievements/', verbose_name="Файл грамоты")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено')
    ], default='pending')
    quantics_reward = models.PositiveIntegerField(default=0, verbose_name="Награда в квантиках")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey('shop.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_achievements')

    def __str__(self):
        return f"{self.title} - {self.user.username}"
class PendingUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    kvantum = models.CharField(max_length=10, choices=KVANTUM_CHOICES)  # Используем KVANTUM_CHOICES
    password = models.CharField(max_length=128)  # Хэшированный пароль
    code = models.CharField(max_length=6)  # Код подтверждения
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания

    def is_expired(self):
        # Код действителен 10 минут
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))  # Генерация 6-значного кода

    def __str__(self):
        return f"Pending user: {self.email}"


class EmailConfirmation(models.Model):
    user = models.OneToOneField('shop.User', on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))  # Генерация 6-значного кода

    def is_expired(self):
        # Код действителен 10 минут
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

    def __str__(self):
        return f"Confirmation for {self.user.email}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        'shop.User',
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    quantics = models.IntegerField(default=0)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    kvantum = models.CharField(max_length=10, choices=KVANTUM_CHOICES)  # Используем KVANTUM_CHOICES
    is_approved = models.BooleanField(default=False)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название товара")
    description = models.TextField(verbose_name="Описание товара")
    price = models.IntegerField(verbose_name="Цена")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    image = models.ImageField(upload_to='products/', verbose_name="Изображение", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.PositiveIntegerField()
    is_completed = models.BooleanField(default=False)


    def __str__(self):
        return f"Заказ #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()  # Сохраняем цену на момент заказа

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"