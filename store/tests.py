from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Product, Cart, CartItem, Order, OrderItem

User = get_user_model()


class ProductStoreTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='Password123!',
            email='admin@test.com',
            role=User.ROLE_ADMIN
        )
        self.seller_1 = User.objects.create_user(
            username='seller_one',
            password='Password123!',
            email='seller1@test.com',
            role=User.ROLE_SELLER
        )
        self.seller_2 = User.objects.create_user(
            username='seller_two',
            password='Password123!',
            email='seller2@test.com',
            role=User.ROLE_SELLER
        )
        self.buyer = User.objects.create_user(
            username='buyer_user',
            password='Password123!',
            email='buyer@test.com',
            role=User.ROLE_BUYER
        )

        # Categories
        self.cat_birthday = Category.objects.create(
            name='Birthday Cards',
            slug='birthday-cards',
            description='Celebration cards'
        )
        self.cat_wedding = Category.objects.create(
            name='Wedding Cards',
            slug='wedding-cards',
            description='Wedding and anniversary'
        )

        # Products
        self.prod_1 = Product.objects.create(
            seller=self.seller_1,
            category=self.cat_birthday,
            title='Gold Foil Birthday Card',
            description='Sparkling gold foil lettering on textured paper.',
            price=Decimal('5.99'),
            stock=20,
            image_url='https://example.com/card1.jpg'
        )
        self.prod_2 = Product.objects.create(
            seller=self.seller_1,
            category=self.cat_wedding,
            title='Silver Floral Wedding Card',
            description='Romantic floral wreath with silver accent.',
            price=Decimal('12.50'),
            stock=15,
            image_url='https://example.com/card2.jpg'
        )
        self.prod_3 = Product.objects.create(
            seller=self.seller_2,
            category=self.cat_birthday,
            title='Whimsical Balloon Birthday Card',
            description='Fun and colorful balloon illustrated card.',
            price=Decimal('4.50'),
            stock=30,
            image_url='https://example.com/card3.jpg'
        )

    def test_category_list(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Verify product count annotation
        birthday_cat = next(c for c in response.data if c['slug'] == 'birthday-cards')
        self.assertEqual(birthday_cat['product_count'], 2)

    def test_product_list_unauthenticated(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_product_filter_by_category(self):
        response = self.client.get(f'/api/products/?category={self.cat_wedding.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Silver Floral Wedding Card')

    def test_product_search(self):
        response = self.client.get('/api/products/?search=balloon')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.prod_3.id)

    def test_product_sorting_price_asc(self):
        response = self.client.get('/api/products/?ordering=price_asc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [float(p['price']) for p in response.data]
        self.assertEqual(prices, [4.50, 5.99, 12.50])

    def test_product_detail(self):
        response = self.client.get(f'/api/products/{self.prod_1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Gold Foil Birthday Card')
        self.assertTrue(response.data['is_in_stock'])

    def test_seller_can_create_product(self):
        self.client.force_authenticate(user=self.seller_1)
        payload = {
            'title': 'New Artisan Card',
            'description': 'Handmade with love.',
            'price': '7.25',
            'stock': 10,
            'category_id': self.cat_birthday.id,
            'image_url': 'https://example.com/card4.jpg'
        }
        response = self.client.post('/api/products/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['seller']['username'], 'seller_one')
        self.assertEqual(Product.objects.count(), 4)

    def test_buyer_cannot_create_product(self):
        self.client.force_authenticate(user=self.buyer)
        payload = {
            'title': 'Buyer Attempt',
            'description': 'Should fail.',
            'price': '5.00',
            'stock': 5
        }
        response = self.client.post('/api/products/', payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_seller_cannot_edit_other_sellers_product(self):
        self.client.force_authenticate(user=self.seller_2)
        # Attempt to edit seller_1's product
        response = self.client.put(f'/api/products/{self.prod_1.id}/', {
            'price': '99.99'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_edit_any_product(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(f'/api/products/{self.prod_1.id}/', {
            'price': '99.99'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.prod_1.refresh_from_db()
        self.assertEqual(self.prod_1.price, Decimal('99.99'))


class CartTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.buyer = User.objects.create_user(
            username='cart_buyer',
            password='Password123!',
            email='cartbuyer@test.com',
            role=User.ROLE_BUYER
        )
        self.seller = User.objects.create_user(
            username='cart_seller',
            password='Password123!',
            email='cartseller@test.com',
            role=User.ROLE_SELLER
        )
        self.product = Product.objects.create(
            seller=self.seller,
            title='Artisan Birthday Card',
            description='Handmade card',
            price=Decimal('10.00'),
            stock=5
        )

    def test_unauthenticated_cart_access_denied(self):
        response = self.client.get('/api/cart/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_cart_creates_new(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(float(response.data['total_price']), 0.0)

    def test_add_to_cart_success(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post('/api/cart/items/', {
            'product_id': self.product.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(float(response.data['total_price']), 20.00)

    def test_add_to_cart_stacks_quantity(self):
        self.client.force_authenticate(user=self.buyer)
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})
        response = self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 3)
        self.assertEqual(float(response.data['total_price']), 30.00)

    def test_add_to_cart_exceeding_stock_fails(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post('/api/cart/items/', {
            'product_id': self.product.id,
            'quantity': 10  # Stock is only 5
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_update_cart_item_quantity(self):
        self.client.force_authenticate(user=self.buyer)
        add_resp = self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})
        item_id = add_resp.data['items'][0]['id']

        update_resp = self.client.patch(f'/api/cart/items/{item_id}/', {'quantity': 4})
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data['total_items'], 4)
        self.assertEqual(float(update_resp.data['total_price']), 40.00)

    def test_remove_cart_item(self):
        self.client.force_authenticate(user=self.buyer)
        add_resp = self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 2})
        item_id = add_resp.data['items'][0]['id']

        del_resp = self.client.delete(f'/api/cart/items/{item_id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(del_resp.data['total_items'], 0)

    def test_clear_cart(self):
        self.client.force_authenticate(user=self.buyer)
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})
        clear_resp = self.client.delete('/api/cart/clear/')
        self.assertEqual(clear_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(clear_resp.data['total_items'], 0)


class OrderCheckoutTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='order_admin',
            password='Password123!',
            email='admin@orders.com',
            role=User.ROLE_ADMIN
        )
        self.seller = User.objects.create_user(
            username='order_seller',
            password='Password123!',
            email='seller@orders.com',
            role=User.ROLE_SELLER
        )
        self.buyer_1 = User.objects.create_user(
            username='order_buyer_1',
            password='Password123!',
            email='buyer1@orders.com',
            role=User.ROLE_BUYER
        )
        self.buyer_2 = User.objects.create_user(
            username='order_buyer_2',
            password='Password123!',
            email='buyer2@orders.com',
            role=User.ROLE_BUYER
        )
        self.product = Product.objects.create(
            seller=self.seller,
            title='Deluxe Keepsake Card',
            description='Handmade keepsake card',
            price=Decimal('15.00'),
            stock=10
        )

    def test_checkout_empty_cart_fails(self):
        self.client.force_authenticate(user=self.buyer_1)
        payload = {
            'full_name': 'Test Buyer',
            'shipping_address': '123 Test St',
            'city': 'Testville',
            'postal_code': '12345',
            'phone': '555-0100'
        }
        response = self.client.post('/api/orders/checkout/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_success_creates_order_and_deducts_stock(self):
        self.client.force_authenticate(user=self.buyer_1)
        # Add 3 items to cart
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 3})

        payload = {
            'full_name': 'Test Buyer',
            'shipping_address': '123 Test St',
            'city': 'Testville',
            'postal_code': '12345',
            'phone': '555-0100'
        }
        response = self.client.post('/api/orders/checkout/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'Pending')
        self.assertEqual(float(response.data['total_amount']), 45.00)
        self.assertEqual(len(response.data['items']), 1)

        # Check stock deduction
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)  # 10 - 3 = 7

        # Check cart cleared
        cart = Cart.objects.get(user=self.buyer_1)
        self.assertEqual(cart.items.count(), 0)

    def test_checkout_insufficient_stock_fails_and_preserves_stock(self):
        self.client.force_authenticate(user=self.buyer_1)
        # Add 5 items to cart
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 5})

        # Artificially drop stock to 2 in DB
        self.product.stock = 2
        self.product.save()

        payload = {
            'full_name': 'Test Buyer',
            'shipping_address': '123 Test St',
            'city': 'Testville',
            'postal_code': '12345',
            'phone': '555-0100'
        }
        response = self.client.post('/api/orders/checkout/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['detail'])

        # Stock is still 2
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_buyer_isolation_in_order_list(self):
        # Create order for buyer 1
        Order.objects.create(
            buyer=self.buyer_1,
            total_amount=Decimal('15.00'),
            full_name='Buyer 1',
            shipping_address='Street 1',
            city='City 1',
            postal_code='11111',
            phone='111'
        )
        # Create order for buyer 2
        Order.objects.create(
            buyer=self.buyer_2,
            total_amount=Decimal('30.00'),
            full_name='Buyer 2',
            shipping_address='Street 2',
            city='City 2',
            postal_code='22222',
            phone='222'
        )

        # Buyer 1 checks orders
        self.client.force_authenticate(user=self.buyer_1)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['full_name'], 'Buyer 1')

        # Admin checks orders
        self.client.force_authenticate(user=self.admin)
        admin_resp = self.client.get('/api/orders/')
        self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(admin_resp.data), 2)

    def test_order_cancellation_restores_stock(self):
        order = Order.objects.create(
            buyer=self.buyer_1,
            total_amount=Decimal('30.00'),
            full_name='Buyer 1',
            shipping_address='Street 1',
            city='City 1',
            postal_code='11111',
            phone='111'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_title=self.product.title,
            seller=self.seller,
            price=self.product.price,
            quantity=2
        )
        # Manually lower stock to simulate purchase
        self.product.stock = 8
        self.product.save()

        # Admin cancels order
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'Cancelled'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Cancelled')

        # Stock is restored back to 10
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)


class DashboardTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='dash_admin',
            password='Password123!',
            email='admin@dash.com',
            role=User.ROLE_ADMIN
        )
        self.seller = User.objects.create_user(
            username='dash_seller',
            password='Password123!',
            email='seller@dash.com',
            role=User.ROLE_SELLER
        )
        self.buyer = User.objects.create_user(
            username='dash_buyer',
            password='Password123!',
            email='buyer@dash.com',
            role=User.ROLE_BUYER
        )
        self.product = Product.objects.create(
            seller=self.seller,
            title='Artisan Thank You Card',
            description='Warm gratitude',
            price=Decimal('8.00'),
            stock=25
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            total_amount=Decimal('16.00'),
            full_name='Dashboard Buyer',
            shipping_address='77 Broadway',
            city='New York',
            postal_code='10001',
            phone='555-0155',
            status=Order.STATUS_PENDING
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title=self.product.title,
            seller=self.seller,
            price=Decimal('8.00'),
            quantity=2
        )

    def test_admin_dashboard_permissions(self):
        # Anonymous
        resp = self.client.get('/api/dashboard/admin/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Buyer
        self.client.force_authenticate(user=self.buyer)
        buyer_resp = self.client.get('/api/dashboard/admin/')
        self.assertEqual(buyer_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Admin
        self.client.force_authenticate(user=self.admin)
        admin_resp = self.client.get('/api/dashboard/admin/')
        self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_resp.data['stats']['total_orders'], 1)
        self.assertEqual(admin_resp.data['stats']['total_revenue'], 16.00)
        self.assertEqual(admin_resp.data['stats']['pending_orders'], 1)

    def test_seller_dashboard_metrics(self):
        # Buyer cannot access
        self.client.force_authenticate(user=self.buyer)
        buyer_resp = self.client.get('/api/dashboard/seller/')
        self.assertEqual(buyer_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Seller
        self.client.force_authenticate(user=self.seller)
        seller_resp = self.client.get('/api/dashboard/seller/')
        self.assertEqual(seller_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(seller_resp.data['stats']['total_products'], 1)
        self.assertEqual(seller_resp.data['stats']['total_units_sold'], 2)
        self.assertEqual(seller_resp.data['stats']['total_earnings'], 16.00)
        self.assertEqual(len(seller_resp.data['orders']), 1)
