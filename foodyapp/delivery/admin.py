from django.contrib import admin
from .models import Customer
from .models import Restaurant
from .models import MenuItem
from .models import Order
from .models import OrderItem
admin.site.register(Customer)
admin.site.register(Restaurant)
admin.site.register(MenuItem)
admin.site.register(Order)
admin.site.register(OrderItem)
