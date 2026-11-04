from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import IsSellerRole, IsAdminRole
from accounts.serializers import UserSerializer
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryListView(APIView):
    """
    Public API: List all product categories.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductListCreateView(APIView):
    """
    Public API: List products with category filter, search, and sorting.
    Protected API (POST): Create a new product (Sellers/Admin only).
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSellerRole()]
        return [AllowAny()]

    def get(self, request):
        queryset = Product.objects.filter(is_active=True).select_related('seller', 'category')

        # Filter by category (by ID or by Slug)
        category_param = request.query_params.get('category')
        if category_param:
            if category_param.isdigit():
                queryset = queryset.filter(category_id=category_param)
            else:
                queryset = queryset.filter(category__slug=category_param)

        # Search query (title, description)
        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Sorting
        ordering = request.query_params.get('ordering', 'newest')
        if ordering == 'price_asc':
            queryset = queryset.order_by('price')
        elif ordering == 'price_desc':
            queryset = queryset.order_by('-price')
        elif ordering == 'name_asc':
            queryset = queryset.order_by('title')
        elif ordering == 'name_desc':
            queryset = queryset.order_by('-title')
        else:  # newest
            queryset = queryset.order_by('-created_at')

        serializer = ProductSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response(
                ProductSerializer(product, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    """
    Retrieve, update, or delete an individual product.
    Updates and Deletions are restricted to the product's seller or an Admin.
    """
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsSellerRole()]
        return [AllowAny()]

    def get_object(self, pk):
        try:
            return Product.objects.select_related('seller', 'category').get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check ownership: seller must own product, or user must be admin
        if product.seller != request.user and not request.user.is_admin_role:
            return Response(
                {'detail': 'You do not have permission to edit this product.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ProductSerializer(product, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if product.seller != request.user and not request.user.is_admin_role:
            return Response(
                {'detail': 'You do not have permission to delete this product.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Set inactive or delete
        product.delete()
        return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_200_OK)


class SellerProductListView(APIView):
    """
    API for Sellers to retrieve all of their owned products.
    """
    permission_classes = [IsAuthenticated, IsSellerRole]

    def get(self, request):
        if request.user.is_admin_role:
            products = Product.objects.all().select_related('seller', 'category')
        else:
            products = Product.objects.filter(seller=request.user).select_related('seller', 'category')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==============================================================================
# Cart Views
# ==============================================================================

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)


class CartDetailView(APIView):
    """
    Retrieve or initialize the authenticated user's shopping cart.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemAddView(APIView):
    """
    Add a product to the user's cart or increase quantity if it already exists.
    Enforces product stock limits.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response({
                    'detail': f"Cannot add {quantity} more. Only {product.stock} available in stock (you already have {cart_item.quantity} in cart)."
                }, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            if quantity > product.stock:
                cart_item.delete()
                return Response({
                    'detail': f"Only {product.stock} available in stock."
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class CartItemDetailView(APIView):
    """
    Update quantity or remove an item from the user's cart.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        try:
            cart_item = CartItem.objects.select_related('cart', 'product').get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_quantity = serializer.validated_data['quantity']
        if new_quantity > cart_item.product.stock:
            return Response({
                'detail': f"Only {cart_item.product.stock} items currently in stock."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = new_quantity
        cart_item.save()

        return Response(
            CartSerializer(cart_item.cart).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.select_related('cart').get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart = cart_item.cart
        cart_item.delete()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class CartClearView(APIView):
    """
    Remove all items from the current user's cart.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


# ==============================================================================
# Order Views & Checkout Processing
# ==============================================================================

from django.db import transaction
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    CheckoutSerializer,
)


class CheckoutView(APIView):
    """
    Processes customer checkout:
    1. Validates shipping information
    2. Verifies stock availability
    3. Atomically deducts stock & generates Order + OrderItems
    4. Empties the user's cart
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({'detail': 'Cart not found.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = list(cart.items.select_related('product', 'product__seller').all())
        if not cart_items:
            return Response({'detail': 'Your shopping cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Atomic transaction to guarantee data integrity during stock deduction
        with transaction.atomic():
            # Verify stock for every item
            for item in cart_items:
                if item.product.stock < item.quantity:
                    return Response({
                        'detail': f"Insufficient stock for '{item.product.title}'. Only {item.product.stock} item(s) left."
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Deduct stock
            for item in cart_items:
                item.product.stock -= item.quantity
                item.product.save(update_fields=['stock'])

            # Create Order
            order = Order.objects.create(
                buyer=request.user,
                total_amount=cart.total_price,
                status=Order.STATUS_PENDING,
                full_name=serializer.validated_data['full_name'],
                shipping_address=serializer.validated_data['shipping_address'],
                city=serializer.validated_data['city'],
                postal_code=serializer.validated_data['postal_code'],
                phone=serializer.validated_data['phone']
            )

            # Create Order Items snapshot
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_title=item.product.title,
                    seller=item.product.seller,
                    price=item.product.price,
                    quantity=item.quantity
                )

            # Clear Cart
            cart.items.all().delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderListView(APIView):
    """
    List orders:
    - Buyers: see their own past orders
    - Admins: see all platform orders
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_admin_role:
            orders = Order.objects.all().select_related('buyer').prefetch_related('items__product')
        else:
            orders = Order.objects.filter(buyer=request.user).select_related('buyer').prefetch_related('items__product')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """
    Retrieve details of a specific order.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.select_related('buyer').prefetch_related('items__product').get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check access permission: buyer, admin, or seller of items
        is_seller_of_item = order.items.filter(seller=request.user).exists()
        if order.buyer != request.user and not request.user.is_admin_role and not is_seller_of_item:
            return Response({'detail': 'Access denied to this order.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderStatusUpdateView(APIView):
    """
    Update order fulfillment status (Pending, Shipped, Delivered, Cancelled).
    Restricted to Admins and Sellers.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only seller involved or admin can update status
        is_seller = order.items.filter(seller=request.user).exists()
        if not request.user.is_admin_role and not is_seller:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({
                'detail': f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # If transitioning to Cancelled, return stock
        if new_status == Order.STATUS_CANCELLED and order.status != Order.STATUS_CANCELLED:
            for item in order.items.select_related('product').all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])

        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


# ==============================================================================
# Dashboard Views (Admin & Seller Analytics & Management)
# ==============================================================================

from django.db.models import Sum, Count, F
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminDashboardView(APIView):
    """
    Consolidated analytics and management endpoint for Platform Administrators.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        # 1. Platform Statistics
        non_cancelled_orders = Order.objects.exclude(status=Order.STATUS_CANCELLED)
        total_revenue = non_cancelled_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).count()
        total_products = Product.objects.filter(is_active=True).count()

        total_users = User.objects.count()
        total_sellers = User.objects.filter(role=User.ROLE_SELLER).count()
        total_buyers = User.objects.filter(role=User.ROLE_BUYER).count()

        # 2. Recent Orders
        recent_orders = Order.objects.select_related('buyer').prefetch_related('items__product').order_by('-created_at')[:20]

        # 3. All Products
        products = Product.objects.select_related('seller', 'category').order_by('-created_at')[:50]

        # 4. Registered Users
        users = User.objects.all().order_by('-date_joined')[:30]

        return Response({
            'stats': {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_products': total_products,
                'total_users': total_users,
                'total_sellers': total_sellers,
                'total_buyers': total_buyers,
            },
            'recent_orders': OrderSerializer(recent_orders, many=True).data,
            'products': ProductSerializer(products, many=True, context={'request': request}).data,
            'users': UserSerializer(users, many=True).data,
        }, status=status.HTTP_200_OK)


class SellerDashboardView(APIView):
    """
    Consolidated metrics, catalog management, and order fulfillment for Sellers.
    """
    permission_classes = [IsAuthenticated, IsSellerRole]

    def get(self, request):
        seller = request.user

        # 1. Seller's Products
        my_products = Product.objects.filter(seller=seller).select_related('category').order_by('-created_at')
        total_products = my_products.count()

        # 2. Orders containing this seller's items
        seller_order_items = OrderItem.objects.filter(seller=seller).select_related('order', 'order__buyer', 'product').order_by('-order__created_at')

        # Filter out cancelled orders for revenue calculation
        valid_items = seller_order_items.exclude(order__status=Order.STATUS_CANCELLED)
        
        # Calculate total earnings and units sold
        total_earnings = sum(item.subtotal for item in valid_items)
        total_units_sold = sum(item.quantity for item in valid_items)
        pending_fulfillments = seller_order_items.filter(order__status=Order.STATUS_PENDING).count()

        # Format items with order metadata for the dashboard table
        orders_data = []
        for item in seller_order_items[:30]:
            orders_data.append({
                'order_id': item.order.id,
                'order_date': item.order.created_at,
                'buyer_username': item.order.buyer.username,
                'product_title': item.product_title,
                'product_image_url': item.product.get_image_url if item.product else 'https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=200&auto=format&fit=crop&q=60',
                'quantity': item.quantity,
                'price': float(item.price),
                'subtotal': float(item.subtotal),
                'status': item.order.status,
                'shipping_address': f"{item.order.full_name}, {item.order.shipping_address}, {item.order.city} (Phone: {item.order.phone})",
            })

        return Response({
            'stats': {
                'total_products': total_products,
                'total_units_sold': total_units_sold,
                'total_earnings': float(total_earnings),
                'pending_fulfillments': pending_fulfillments,
            },
            'products': ProductSerializer(my_products, many=True, context={'request': request}).data,
            'orders': orders_data,
        }, status=status.HTTP_200_OK)
