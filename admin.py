from django.contrib import admin

from mystock.forms import StockCreateForm
# Register your models here.
from mystock.models import Stock, Category

from mystock import models
class StockCreateAdmin(admin.ModelAdmin):
   list_display = ['category', 'item_name', 'quantity']
   form = StockCreateForm
   list_filter = ['category']
   search_fields = ['category', 'item_name']




admin.site.register(Stock, StockCreateAdmin)
admin.site.register(Category)
