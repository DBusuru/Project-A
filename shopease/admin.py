from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from shopease.models import CartItem, Product, Category, Brand, ProductVariant, Review, Order, OrderItem, Wishlist

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'sales_count', 'stock', 'sales_chart')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-sales_count',)
    
    def sales_chart(self, obj):
        """Create a simple visual bar chart for sales"""
        max_sales = Product.objects.aggregate(max_sales=Sum('sales_count'))['max_sales'] or 1
        percentage = (obj.sales_count / max_sales) * 100
        return format_html(
            '<div style="background-color: #0073e6; width: {}%; height: 20px; '
            'border-radius: 3px;" title="{} sales">&nbsp;</div>',
            min(percentage, 100),
            obj.sales_count
        )
    sales_chart.short_description = 'Sales Performance'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ('sales_count',) + self.readonly_fields
        return self.readonly_fields

    def changelist_view(self, request, extra_context=None):
        # Get sales statistics
        extra_context = extra_context or {}
        extra_context['total_sales'] = Product.objects.aggregate(
            total_sales=Sum('sales_count')
        )['total_sales'] or 0
        
        # Get top 5 selling products
        top_products = Product.objects.order_by('-sales_count')[:5]
        extra_context['top_products'] = top_products
        
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {
            'all': ('admin/css/sales_dashboard.css',)
        }

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(CartItem)
admin.site.register(Brand)
admin.site.register(ProductVariant)
admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Wishlist)