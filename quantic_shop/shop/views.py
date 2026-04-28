from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .forms import RegisterForm, ProductForm, AchievementForm, ReviewAchievementForm, AddToCartForm, UpdateCartItemForm
from .models import PendingUser, UserProfile, Product, Achievement, User, Order, OrderItem, Cart, CartItem, Product
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .decorators import kvantum_admin_required, approved_user
from .constants import KVANTUM_CHOICES
def is_admin(user):
    return user.is_staff
@approved_user
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'cart/user_orders.html', {'orders': orders, 'title':'Мои заказы'})

@approved_user
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    # Проверяем, что корзина не пуста
    if not cart.items.exists():
        messages.error(request, "Ваша корзина пуста")
        return redirect('view_cart')

    # Проверяем наличие всех товаров
    for item in cart.items.all():
        if item.quantity > item.product.quantity:
            messages.error(request,
                           f"Товара '{item.product.name}' осталось только {item.product.quantity} шт.")
            return redirect('view_cart')

    # Проверяем баланс
    if request.user.userprofile.quantics < cart.total_price:
        messages.error(request, "Недостаточно квантиков для покупки")
        return redirect('view_cart')

    # Создаем заказ
    order = Order.objects.create(
        user=request.user,
        total_price=cart.total_price
    )

    # Переносим товары в заказ и уменьшаем количество
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

        # Уменьшаем количество товара
        item.product.quantity -= item.quantity
        item.product.save()

    # Списываем квантики
    request.user.userprofile.quantics -= cart.total_price
    request.user.userprofile.save()

    # Очищаем корзину
    cart.items.all().delete()

    messages.success(request, f"Заказ #{order.id} успешно оформлен!")
    return redirect('order_detail', order_id=order.id)


@approved_user
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_detail.html', {'order': order, 'title': 'Информация о заказе'})


# Админские представления
@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'cart/order_list.html', {'orders': orders, 'title': 'Заказы'})


@user_passes_test(is_admin)
def order_admin_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        del order
        return redirect('order_list')

    return render(request, 'cart/order_admin_detail.html', {'order': order, 'title': 'Мои заказы'})
@approved_user
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    balance = request.user.userprofile.quantics
    return render(request, 'cart/cart.html', {'cart': cart, 'balance': balance, 'title': 'Корзина'})


@approved_user
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Проверяем наличие товара
    if product.quantity < 1:
        messages.error(request, "Этот товар временно отсутствует")
        return redirect('home')

    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = 1  # По умолчанию 1

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        # Проверяем, достаточно ли товара на складе
        if quantity > product.quantity:
            messages.error(request, f"Недостаточно товара. Доступно: {product.quantity}")
            return redirect('home')

    # Добавляем или обновляем товар в корзине
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.quantity:
            messages.error(request, f"Нельзя добавить больше {product.quantity} шт.")
            return redirect('home')
        cart_item.quantity = new_quantity
        cart_item.save()

    messages.success(request, f"Товар {product.name} добавлен в корзину")
    return redirect('home')


@approved_user
def update_cart(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)

        for item in cart.items.all():
            new_quantity = int(request.POST.get(f'quantity_{item.id}', item.quantity))

            # Проверяем наличие товара
            if new_quantity > item.product.quantity:
                messages.error(request,
                               f"Недостаточно товара '{item.product.name}'. Доступно: {item.product.quantity}")
                return redirect('view_cart')

            if new_quantity < 1:
                item.delete()
            else:
                item.quantity = new_quantity
                item.save()

        messages.success(request, "Корзина обновлена")
        return redirect('view_cart')

    return redirect('view_cart')


@approved_user
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Товар удален из корзины")
    return redirect('view_cart')




@kvantum_admin_required
def review_achievements(request):
    # Показываем только заявки из квантума админа
    achievements = Achievement.objects.filter(
        status='pending',
        user__userprofile__kvantum=request.user.kvantum
    )
    return render(request, 'achievements/review.html', {'achievements': achievements, 'title':'Заявки грамот'})


@kvantum_admin_required
def review_achievement_detail(request, pk):
    achievement = get_object_or_404(Achievement, pk=pk)

    # Проверяем, что заявка из квантума админа
    if achievement.user.userprofile.kvantum != request.user.kvantum:
        raise PermissionDenied
@approved_user
def submit_achievement(request):
    if not request.user.userprofile.is_approved:
        return redirect('home')
    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            achievement = form.save(commit=False)
            achievement.user = request.user
            achievement.save()
            return redirect('profile')
    else:
        form = AchievementForm()
    return render(request, 'achievements/submit_achievement.html', {'form': form,'title':'Отправить грамоту'})

@user_passes_test(is_admin)
def review_achievements(request):
    achievements = Achievement.objects.filter(status='pending')
    return render(request, 'achievements/review.html', {'achievements': achievements,'title':'Список грамот'})


@user_passes_test(is_admin)
def review_achievement_detail(request, pk):
    achievement = get_object_or_404(Achievement, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            quantics_reward = int(request.POST.get('quantics_reward', 0))
            achievement.status = 'approved'
            achievement.quantics_reward = quantics_reward
            achievement.reviewed_by = request.user

            # Начисляем награду
            profile = achievement.user.userprofile
            profile.quantics += quantics_reward
            profile.save()

            messages.success(request, f'Грамота одобрена! Начислено {quantics_reward} квантиков.')

        elif action == 'reject':
            achievement.status = 'rejected'
            achievement.reviewed_by = request.user
            messages.warning(request, 'Грамота отклонена.')

        achievement.save()
        return redirect('review_achievements')

    return render(request, 'achievements/review_detail.html', {'achievement': achievement,'title':'Рассмотрение грамот'})


# Список товаров
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'admin/product_list.html', {'products': products,'title':'Список товаров'})

# Добавление товара
@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'admin/add_product.html', {'form': form,'title':'Редактирование товаров'})

# Редактирование товара
@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin/edit_product.html', {'form': form, 'product': product,'title':'Редактирование товаров'})

# Удаление товара
@user_passes_test(is_admin)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'admin/confirm_delete.html', {'product': product})


@kvantum_admin_required
def admin_approve_profiles(request):
    # Фильтруем по квантуму администратора
    unapproved_profiles = UserProfile.objects.filter(
        is_approved=False,
        kvantum=request.user.admin_kvantum
    ).select_related('user')
    kvantum_display = dict(KVANTUM_CHOICES).get(request.user.admin_kvantum, request.user.admin_kvantum)
    return render(request, 'registration/approve_profiles.html', {
        'unapproved_profiles': unapproved_profiles,
        'current_kvantum': kvantum_display,
        'title':'Подтверждение пользователей'
    })


@kvantum_admin_required
def admin_approve_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)

    # Проверяем соответствие квантума
    if profile.kvantum != request.user.admin_kvantum:
        raise PermissionDenied

    profile.is_approved = True
    profile.save()
    messages.success(request, f"Профиль {profile.user.username} подтвержден")
    return redirect('admin_approve_profiles')

@user_passes_test(is_admin)
def admin_delete_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)
    if request.method == 'POST':
        profile.user.delete()  # Удаляем пользователя и его профиль (если on_delete=CASCADE)
        messages.success(request, f"Профиль пользователя {profile.user.username} удален.")
        return redirect('admin_approve_profiles')
    return render(request, 'registration/confirm_delete_profile.html', {'profile': profile})

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                pending_user = form.save(commit=False)  # Сохраняем данные во временный объект
                send_confirmation_email(pending_user)  # Отправляем код подтверждения
                messages.success(request, "Пожалуйста, подтвердите ваш email.")
                return redirect('confirm_email')
            except ValidationError as e:
                form.add_error(None, e.message)  # Добавляем ошибку в форму
        return render(request, 'registration/register.html', {'form': form, 'title':'Регистрация'})
    else:
        form = RegisterForm()
        return render(request, 'registration/register.html', {'form': form, 'title':'Регистрация'})

def send_confirmation_email(pending_user):
    subject = 'Подтверждение почты'
    html_content = render_to_string('registration/mail.html', {
        'confirmation_code': pending_user.code,
    })
    text_content = strip_tags(html_content)  # Текстовая версия письма

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.EMAIL_HOST_USER,
        [pending_user.email],
    )
    email.attach_alternative(html_content, "text/html")  # Добавляем HTML-версию
    email.send()

def confirm_email(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        if 'resend_code' in request.POST:  # Проверяем, была ли нажата кнопка "Отправить новый код"
            email = request.POST.get('email')  # Получаем email из формы
            try:
                pending_user = PendingUser.objects.get(email=email)
                # Генерируем новый код
                pending_user.code = PendingUser.generate_code()
                pending_user.created_at = timezone.now()  # Обновляем время создания кода
                pending_user.save()
                # Отправляем новый код на email
                send_confirmation_email(pending_user)
                messages.success(request, "Новый код подтверждения отправлен на ваш email.")
                return redirect('confirm_email')
            except PendingUser.DoesNotExist:
                messages.error(request, "Пользователь с таким email не найден.")
                return redirect('confirm_email')

        code = request.POST.get('confirmation_code')
        try:
            pending_user = PendingUser.objects.get(code=code)
            if pending_user.is_expired():
                messages.error(request, "Срок действия кода истёк. Зарегистрируйтесь снова.")
                pending_user.delete()
                return redirect('register')

            # Создаем пользователя
            user = User(
                username=pending_user.username,
                email=pending_user.email,
                first_name=pending_user.first_name,
                last_name=pending_user.last_name,
                password=make_password(pending_user.password),
                is_active=True
            )
            user.save()

            # Создаем профиль пользователя
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'quantics': 0,
                    'first_name': pending_user.first_name,
                    'last_name': pending_user.last_name,
                    'age': pending_user.age,
                    'kvantum': pending_user.kvantum,  # Убедитесь, что квантум передается корректно
                    'is_approved': False
                }
            )

            # Удаляем временный объект
            pending_user.delete()

            messages.success(request, "Ваш email успешно подтвержден! Теперь вы можете войти в систему.")
            return redirect('login')
        except PendingUser.DoesNotExist:
            messages.error(request, "Неверный код подтверждения.")
    return render(request, 'registration/confirm_email.html',{'title':'Подтверждение почты'})

def home(request):
    if request.user.is_authenticated:
        try:
            # Получаем профиль пользователя
            profile = request.user.userprofile
            if not profile.is_approved:
                messages.error(request, "Ваш профиль еще не подтвержден администратором.")
                return render(request, 'main/waiting_approval.html', {'title':'Ожидание Подтверждения'})  # Страница ожидания подтверждения
            return redirect('profile')  # Перенаправляем в профиль, если он подтвержден
        except UserProfile.DoesNotExist:
            # Если профиль не существует, создаем его
            profile = UserProfile.objects.create(
                user=request.user,
                quantics=0,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                age=18,  # Укажите значение по умолчанию
                kvantum='IT',  # Укажите значение по умолчанию
                is_approved=False  # По умолчанию профиль не подтвержден
            )
            messages.error(request, "Ваш профиль еще не подтвержден администратором.")
            return render(request, 'main/waiting_approval.html', {'title':'Ожидание Подтверждения'})  # Страница ожидания подтверждения
    else:
        products = Product.objects.filter(quantity__gt=0)
        return render(request, 'main/guest_home.html', {'title':'Квантомаркет', 'products': products,})  # Показываем страницу для гостей


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:  # Проверяем, активен ли пользователь
                auth_login(request, user)
                return redirect('profile')
            else:
                messages.error(request, 'Ваш аккаунт не активирован. Пожалуйста, подтвердите email.')
                return redirect('confirm_email')
        else:
            print("Ошибка авторизации")
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'registration/login.html', {'title':'Авторизация'})

@approved_user
def user_profile(request):
    try:
        profile = request.user.userprofile
        if not profile.is_approved:
            messages.error(request, "Ваш профиль еще не подтвержден администратором.")
            return redirect('home')  # Перенаправляем на главную страницу
    except UserProfile.DoesNotExist:
        # Если профиль не существует, создаем его
        profile = UserProfile.objects.create(
            user=request.user,
            quantics=0,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            age=18,  # Укажите значение по умолчанию
            kvantum='IT',  # Укажите значение по умолчанию
            is_approved=False  # По умолчанию профиль не подтвержден
        )
        messages.error(request, "Ваш профиль еще не подтвержден администратором.")
        return redirect('home')

    products = Product.objects.filter(quantity__gt=0)

    return render(request, 'main/index.html', {'profile': profile, 'products': products, 'title':'Квантомаркет', })