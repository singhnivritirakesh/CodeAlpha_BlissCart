from decimal import Decimal
from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Category, Product, Cart, CartItem, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for product categories with product count.
    """
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """
    Comprehensive product serializer for listing and detail views.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    seller = UserSerializer(read_only=True)
    image_display_url = serializers.ReadOnlyField(source='get_image_url')
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'seller',
            'category',
            'category_id',
            'title',
            'slug',
            'description',
            'price',
            'stock',
            'image',
            'image_url',
            'image_display_url',
            'is_in_stock',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'seller', 'created_at', 'updated_at', 'image_display_url', 'is_in_stock']

    def validate_price(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def create(self, validated_data):
        # Automatically assign the logged-in seller as the product owner
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['seller'] = request.user
        return super().create(validated_data)



# ==============================================================================
# Cart Serializers
# ==============================================================================

class CartProductSerializer(serializers.ModelSerializer):
    """
    Lightweight product representation inside cart items.
    """
    image_display_url = serializers.ReadOnlyField(source='get_image_url')
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'slug',
            'price',
            'stock',
            'image_display_url',
            'is_in_stock',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for items stored within a cart.
    """
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'quantity',
            'subtotal',
            'created_at',
            'updated_at',
        ]


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for the customer shopping cart including all items and totals.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'total_items',
            'total_price',
            'created_at',
            'updated_at',
        ]


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer to validate adding a product to the cart.
    """
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)

    def validate(self, attrs):
        product_id = attrs.get('product_id')
        quantity = attrs.get('quantity', 1)

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found or is currently unavailable."})

        if product.stock <= 0:
            raise serializers.ValidationError({"quantity": "Sorry, this product is completely out of stock."})

        attrs['product'] = product
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer to validate updating an existing cart item quantity.
    """
    quantity = serializers.IntegerField(required=True, min_value=1)


# ==============================================================================
# Order Serializers
# ==============================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual items purchased in an order.
    """
    seller_username = serializers.ReadOnlyField(source='seller.username')
    product_image_url = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_title',
            'seller',
            'seller_username',
            'product_image_url',
            'price',
            'quantity',
            'subtotal',
        ]

    def get_product_image_url(self, obj):
        if obj.product:
            return obj.product.get_image_url
        return 'https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=500&auto=format&fit=crop&q=60'


class OrderSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for customer orders.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_username = serializers.ReadOnlyField(source='buyer.username')

    class Meta:
        model = Order
        fields = [
            'id',
            'buyer',
            'buyer_username',
            'status',
            'total_amount',
            'full_name',
            'shipping_address',
            'city',
            'postal_code',
            'phone',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'buyer', 'total_amount', 'created_at', 'updated_at']


class CheckoutSerializer(serializers.Serializer):
    """
    Serializer to validate shipping information during checkout.
    """
    full_name = serializers.CharField(max_length=200, required=True)
    shipping_address = serializers.CharField(required=True)
    city = serializers.CharField(max_length=100, required=True)
    postal_code = serializers.CharField(max_length=20, required=True)
    phone = serializers.CharField(max_length=20, required=True)

    def validate_full_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters.")
        return value.strip()

    def validate_shipping_address(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Please provide a valid, complete street address.")
        return value.strip()
