from django.urls import path
from . import views  

urlpatterns = [
    path('', views.home, name='home'),
    # add more paths here
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('check_sign_in/', views.check_sign_in, name='check_sign_in'),
    path('check_sign_up/', views.check_sign_up, name='check_sign_up'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('customer-home/', views.customer_home, name='customer_home'),
    path('add-restaurant/', views.add_restaurant, name='add_restaurant'),
    path('delete-restaurant/<int:id>/', views.delete_restaurant, name='delete_restaurant'),
    path('add-menu-item/<int:restaurant_id>/', views.add_menu_item, name='add_menu_item'),
    path('delete-menu-item/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('place-order/', views.place_order, name='place_order'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('modify-order/<int:order_id>/', views.modify_order, name='modify_order'),
    path('terms-and-condition/', views.terms_and_condition, name='terms_and_condition'),
]
