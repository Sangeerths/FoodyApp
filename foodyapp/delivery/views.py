from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from .models import Customer, Restaurant, MenuItem, Order, OrderItem, CartItem
from .decorators import customer_login_required
import razorpay
import json
from django.utils import timezone
from django.db import models

from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def signin(request):
    return render(request, 'signin.html')

def signup(request):
    return render(request, 'signup.html')

from django.http import HttpResponse
def check_sign_in(request):
    # Simple username/password check against Customer model
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if username == "admin" and password == "admin123":
        request.session['is_admin'] = True
        return redirect('admin_home')
    else:
        try:
            customer = Customer.objects.get(username=username, password=password)
            # Store customer ID in session
            request.session['customer_id'] = customer.id
            return redirect('customer_home')
        except Customer.DoesNotExist:
            # Authentication failed — re-render signin with an error message
            return render(request, 'signin.html', {'error': 'Invalid username or password'})

@customer_login_required
def customer_home(request):
    customer = get_object_or_404(Customer, id=request.session['customer_id'])
    restaurants = Restaurant.objects.prefetch_related('menu_items').all()
    cart_items, cart_total = get_cart_data(customer)
    orders = Order.objects.filter(customer=customer).select_related('restaurant').prefetch_related('orderitem_set', 'orderitem_set__menu_item').order_by('-created_at')
    
    return render(request, 'customer_home.html', {
        'customer': customer,
        'restaurants': restaurants,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'orders': orders
    })        
    

def check_sign_up(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        age = request.POST.get('age')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        street_address = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        password = request.POST.get('password')

        Customer.objects.create(first_name=first_name,
                                last_name=last_name,
                                email=email,
                                username=username,
                                age=age,
                                phone=phone,
                                gender=gender,
                                street_address=street_address,
                                city=city,
                                state=state,
                                pincode=pincode,
                                 password=password)
        return render(request, 'signin.html')

from django.shortcuts import render, redirect
from .models import Restaurant

def add_restaurant(request):
    if not request.session.get('is_admin'):
        return redirect('signin')
    
    if request.method == 'POST':
        restaurant_name = request.POST.get('restaurant_name')
        restaurant_location = request.POST.get('restaurant_location')
        restaurant_contact = request.POST.get('restaurant_contact')
        restaurant_description = request.POST.get('restaurant_description')

        # Create new restaurant
        Restaurant.objects.create(
            restaurant_name=restaurant_name,
            restaurant_location=restaurant_location,
            restaurant_contact=restaurant_contact,
            restaurant_description=restaurant_description
        )

        # Redirect to admin home to fetch updated list
        return redirect('/admin-home/')
  # Make sure 'admin_home' is the URL name of your dashboard

# Dashboard view
def admin_home(request):
    restaurants = Restaurant.objects.prefetch_related('menu_items').all()
    orders = Order.objects.select_related('customer', 'restaurant').prefetch_related('orderitem_set', 'orderitem_set__menu_item').order_by('-created_at')
    total_orders = orders.filter(status='Delivered').count()
    today = timezone.now().date()
    today_revenue = orders.filter(status='Delivered', created_at__date=today).aggregate(total=models.Sum('total'))['total'] or 0
    return render(request, 'admin_home.html', {
        'restaurants': restaurants,
        'orders': orders,
        'total_orders': total_orders,
        'today_revenue': today_revenue
    })

def delete_restaurant(request, id):
    if not request.session.get('is_admin'):
        return redirect('signin')
    
    restaurant = get_object_or_404(Restaurant, id=id)
    restaurant.delete()
    return redirect('admin_home')

def add_menu_item(request, restaurant_id):
    if not request.session.get('is_admin'):
        return redirect('signin')
    
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        item_description = request.POST.get('item_description')
        item_price = request.POST.get('item_price')
        item_category = request.POST.get('item_category')

        MenuItem.objects.create(
            restaurant=restaurant,
            item_name=item_name,
            item_description=item_description,
            item_price=item_price,
            item_category=item_category,
            is_available=True
        )
        return redirect('admin_home')

def delete_menu_item(request, item_id):
    if not request.session.get('is_admin'):
        return redirect('signin')
    
    menu_item = get_object_or_404(MenuItem, id=item_id)
    menu_item.delete()
    return redirect('admin_home')

def get_cart_data(customer):
    """Helper function to get cart items and total"""
    cart_items = CartItem.objects.filter(customer=customer).select_related('menu_item')
    cart_total = sum(item.get_total() for item in cart_items)
    return cart_items, cart_total

@customer_login_required
def add_to_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        customer = get_object_or_404(Customer, id=request.session['customer_id'])
        menu_item = get_object_or_404(MenuItem, id=item_id)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            customer=customer,
            menu_item=menu_item,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, 'Item added to cart successfully!')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect('customer_home')

@customer_login_required
def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        customer = get_object_or_404(Customer, id=request.session['customer_id'])
        cart_item = get_object_or_404(CartItem, customer=customer, menu_item_id=item_id)
        
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return redirect(request.META.get('HTTP_REFERER', '/'))
        
        cart_item.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))

@customer_login_required
def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        customer = get_object_or_404(Customer, id=request.session['customer_id'])
        cart_item = get_object_or_404(CartItem, customer=customer, menu_item_id=item_id)
        cart_item.delete()
        return redirect(request.META.get('HTTP_REFERER', '/'))

@customer_login_required
@transaction.atomic
def place_order(request):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=request.session['customer_id'])
        cart_items = CartItem.objects.filter(customer=customer).select_related('menu_item')
        
        if not cart_items:
            messages.error(request, 'Your cart is empty!')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Calculate total amount for all orders
        total_amount = 0
        orders = []
        
        # Group cart items by restaurant
        restaurant_items = {}
        for cart_item in cart_items:
            restaurant = cart_item.menu_item.restaurant
            if restaurant not in restaurant_items:
                restaurant_items[restaurant] = []
            restaurant_items[restaurant].append(cart_item)
        
        # Create separate orders for each restaurant
        for restaurant, items in restaurant_items.items():
            total = 0
            for cart_item in items:
                item_total = cart_item.menu_item.item_price * cart_item.quantity
                total += item_total
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                status='Pending',
                total=total
            )
            for cart_item in items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.item_price
                )
            orders.append(order)
            total_amount += total
        
        # Store orders in session for payment verification
        request.session['pending_order_ids'] = [order.id for order in orders]
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': int(total_amount * 100),  # Convert to paise
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        # Store cart items in session to clear after successful payment
        request.session['cart_to_clear'] = [cart_item.id for cart_item in cart_items]
        
        return render(request, 'payment_razorpay.html', {
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_amount': int(total_amount * 100),
            'customer': customer,
            'orders': orders,
            'total_amount': total_amount
        })
    
    return redirect('customer_home')

@customer_login_required
def payment_success(request):
    try:
        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        payment_id = request.GET.get('payment_id')
        order_id = request.GET.get('order_id')
        signature = request.GET.get('signature')
        
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        
        # Verify signature
        client.utility.verify_payment_signature(params_dict)
        
        # Update order status
        if 'pending_order_ids' in request.session:
            Order.objects.filter(id__in=request.session['pending_order_ids']).update(status='Processing')
            del request.session['pending_order_ids']
        
        # Clear cart
        if 'cart_to_clear' in request.session:
            CartItem.objects.filter(id__in=request.session['cart_to_clear']).delete()
            del request.session['cart_to_clear']
        
        messages.success(request, 'Payment successful! Your orders have been placed.')
        return redirect('customer_home')
    
    except razorpay.errors.SignatureVerificationError:
        messages.error(request, 'Payment verification failed.')
        return redirect('customer_home')
    except Exception as e:
        messages.error(request, 'An error occurred during payment processing.')
        return redirect('customer_home')

def modify_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully!')
        else:
            messages.error(request, 'Invalid status selected.')
        return redirect('admin_home')
    return render(request, 'modify_order.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES
    })

# Terms and Condition view
def terms_and_condition(request):
    return render(request, 'terms -and-condiion.html')