from .models import PendingUser, Achievement, Product, User, CartItem
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .constants import KVANTUM_CHOICES
from django import forms

class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['title', 'file']

class ReviewAchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['status', 'quantics_reward']
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
        }
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
        }
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
        }
    )
    age = forms.IntegerField(
        required=True,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
        }
    )
    kvantum = forms.ChoiceField(
        choices=KVANTUM_CHOICES,  # Пустой слот
        required=True,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
        }
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'age', 'kvantum', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переопределяем сообщения об ошибках для username, password1, password2
        self.fields['username'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }
        self.fields['password1'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }
        self.fields['password2'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Эта почта уже используется.")
        return email


    def save(self, commit=True):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Эта почта уже используется.")

        PendingUser.objects.filter(email=email).delete()  # Удаляем старые записи

        pending_user = PendingUser(
            username=self.cleaned_data['username'],
            email=email,
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            age=self.cleaned_data['age'],
            kvantum=self.cleaned_data['kvantum'],  # Убедитесь, что квантум передается
            password=self.cleaned_data['password1'],
            code=PendingUser.generate_code()
        )
        pending_user.save()
        return pending_user
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'quantity', 'image']


class AddToCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'max': 100,
                'class': 'form-control',
                'style': 'width: 70px;'
            })
        }

class UpdateCartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'max': 100,
                'class': 'form-control',
                'style': 'width: 70px;'
            })
        }