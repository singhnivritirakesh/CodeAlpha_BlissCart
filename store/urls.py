from django.urls import path
from .views import (
    CategoryListView,
    ProductListCreateView,
    ProductDetailView,
    SellerProductListView,
    CartDetailView,
    CartItemAddView,
    CartItemDetailView,
    CartClearView,
    CheckoutView,
    OrderListView,
    OrderDetailView,
    OrderStatusUpdateView,
    AdminDashboardView,
    SellerDashboardView,
)

app_name = 'store_api'

urlpatterns = [
    # Catalog endpoints
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('products/', ProductListCreateView.as_view(), name='product_list_create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('seller/products/', SellerProductListView.as_view(), name='seller_products'),

    # Cart endpoints
    path('cart/', CartDetailView.as_view(), name='cart_detail'),
    path('cart/items/', CartItemAddView.as_view(), name='cart_item_add'),
    path('cart/items/<int:item_id>/', CartItemDetailView.as_view(), name='cart_item_detail'),
    path('cart/clear/', CartClearView.as_view(), name='cart_clear'),

    # Order & Checkout endpoints
    path('orders/checkout/', CheckoutView.as_view(), name='order_checkout'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order_status_update'),

    # Dashboard Analytics endpoints
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin_dashboard_api'),
    path('dashboard/seller/', SellerDashboardView.as_view(), name='seller_dashboard_api'),
]
