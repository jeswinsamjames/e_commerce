from django.contrib import admin

# Register your models here.
# shop/admin.py
from django.contrib import admin
from .models import *

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Rating)
admin.site.register(Feedback)
