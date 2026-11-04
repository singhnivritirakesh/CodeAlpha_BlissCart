from django.urls import path
from django.views.generic import TemplateView

app_name = 'store_pages'

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('products/<int:pk>/', TemplateView.as_view(template_name='product_detail.html'), name='product_detail_page'),
    path('cart/', TemplateView.as_view(template_name='cart.html'), name='cart_page'),
    path('checkout/', TemplateView.as_view(template_name='checkout.html'), name='checkout_page'),
    path('orders/', TemplateView.as_view(template_name='orders.html'), name='orders_page'),
    path('admin-dashboard/', TemplateView.as_view(template_name='admin_dashboard.html'), name='admin_dashboard_page'),
    path('seller-dashboard/', TemplateView.as_view(template_name='seller_dashboard.html'), name='seller_dashboard_page'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
]
