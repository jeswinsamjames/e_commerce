from django.shortcuts import render

# Create your views here.
# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import ShippingForm, PaymentForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def product_list(request):
    products = Product.objects.all()
    for product in products:
        product.full_stars = int(product.average_rating)
        product.half_star = (product.average_rating - product.full_stars) >= 0.5
        product.empty_stars = 5 - product.full_stars - int(product.half_star)
    return render(request, 'product_list.html', {'products': products})

def product_feedback(request, product_id, feedback_type):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    # Check if the user already submitted feedback for this product
    feedback, created = Feedback.objects.get_or_create(user=user, product=product)

    if feedback_type == 'like':
        feedback.like = not feedback.like if feedback.like is not None else True
    elif feedback_type == 'dislike':
        feedback.like = not feedback.like if feedback.like is not None else False

    feedback.save()

    return JsonResponse({'success': True})

# Update the product_rating view
from django.db.models import Avg

def product_rating(request, product_id, rating):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            user = request.user  # Assuming user is authenticated

            existing_rating = Rating.objects.filter(user=user, product=product).first()
            if existing_rating:
                existing_rating.rating = rating
                existing_rating.save()
            else:
                new_rating = Rating(user=user, product=product, rating=rating)
                new_rating.save()

            # Calculate the average rating dynamically
            average_rating = Rating.objects.filter(product=product).aggregate(avg_rating=Avg('rating'))['avg_rating']

            return JsonResponse({'success': True, 'average_rating': average_rating})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart_detail.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, product_id):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product__id=product_id)
    cart_item.delete()
    return redirect('cart_detail')


@login_required
def checkout_shipping(request):
    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            order = Order.objects.create(user=request.user, total_price=0)  # Calculate the total_price based on the cart items
            shipping_address.order = order
            shipping_address.user = request.user
            shipping_address.save()
            return redirect('checkout_payment')  # Redirect to the next step in your checkout process
    else:
        form = ShippingForm()
    return render(request, 'checkout_shipping.html', {'form': form})


@login_required
def checkout_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            cart = get_object_or_404(Cart, user=request.user)
            order = Order.objects.create(
                user=request.user,
                shipping_address=request.session['shipping_address'],
                billing_address=request.session['billing_address'],
                total_price=cart.get_total_price(),
                is_paid=True,
            )
            for item in cart.cartitem_set.all():
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            cart.cartitem_set.all().delete()
            return redirect('order_confirmation', order_id=order.id)
    else:
        form = PaymentForm()
    return render(request, 'checkout_payment.html', {'form': form})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_confirmation.html', {'order': order})


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('product_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_list.html', {'orders': orders})
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('user_login') 



from django.shortcuts import render
from .models import Product
from .utils import recommend_products  # Import the recommender function

def recommendations(request):
    user_id = request.user.id
    recommended_product_ids = recommend_products(user_id)
    products = Product.objects.filter(id__in=recommended_product_ids)
    return render(request, 'recommendations.html', {'products': products})