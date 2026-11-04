from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Category, Product

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial sample data: Admin, Sellers, Buyers, Categories, and Products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting database seed..."))

        # 1. Create Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@blisscard.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Admin: admin / admin123"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Create Sellers
        seller_john, created = User.objects.get_or_create(
            username='seller_john',
            defaults={
                'email': 'john@blisscard.com',
                'first_name': 'John',
                'last_name': 'Artisan',
                'role': User.ROLE_SELLER,
                'phone_number': '+1-555-0101',
                'address': '742 Evergreen Terrace, Springfield',
            }
        )
        if created:
            seller_john.set_password('seller123')
            seller_john.save()
            self.stdout.write(self.style.SUCCESS("Created Seller: seller_john / seller123"))

        seller_alice, created = User.objects.get_or_create(
            username='seller_alice',
            defaults={
                'email': 'alice@blisscard.com',
                'first_name': 'Alice',
                'last_name': 'Creations',
                'role': User.ROLE_SELLER,
                'phone_number': '+1-555-0102',
                'address': '221B Baker Street, London',
            }
        )
        if created:
            seller_alice.set_password('seller123')
            seller_alice.save()
            self.stdout.write(self.style.SUCCESS("Created Seller: seller_alice / seller123"))

        # 3. Create Buyer
        buyer_bob, created = User.objects.get_or_create(
            username='buyer_bob',
            defaults={
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Customer',
                'role': User.ROLE_BUYER,
                'phone_number': '+1-555-0199',
                'address': '10 Maple Avenue, Riverdale',
            }
        )
        if created:
            buyer_bob.set_password('buyer123')
            buyer_bob.save()
            self.stdout.write(self.style.SUCCESS("Created Buyer: buyer_bob / buyer123"))

        # 4. Create Categories
        categories_data = [
            ("Birthday Cards", "Joyful, creative and heartwarming cards to celebrate another wonderful year."),
            ("Wedding & Anniversary", "Elegant foil, floral and timeless designs for unforgettable milestones."),
            ("Thank You & Gratitude", "Express heartfelt appreciation with elegant and minimalist greeting cards."),
            ("Holiday & Seasonal", "Festive greeting cards for Christmas, New Year, Thanksgiving and more."),
            ("Luxury Gift Sets", "Curated gift cards paired with artisan wax seals, ribbons and envelopes."),
        ]

        categories = {}
        for name, desc in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories[name] = cat
            self.stdout.write(f"Category ensured: {name}")

        # 5. Create Products
        products_data = [
            {
                "seller": seller_john,
                "category": categories["Birthday Cards"],
                "title": "Golden Confetti Pop Birthday Card",
                "description": "Premium 350gsm textured cardstock with embossed gold foil lettering and matching ivory envelope. Perfect for making someone feel truly celebrated.",
                "price": Decimal("6.99"),
                "stock": 45,
                "image_url": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_john,
                "category": categories["Birthday Cards"],
                "title": "Botanical Floral Watercolor Birthday Card",
                "description": "Hand-painted watercolor meadow botanicals with pastel finishes, printed on eco-friendly cotton rag paper.",
                "price": Decimal("5.50"),
                "stock": 30,
                "image_url": "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_alice,
                "category": categories["Wedding & Anniversary"],
                "title": "Eternal Love Laser-Cut Wedding Card",
                "description": "Intricate laser-cut lace design finished with shimmering champagne ribbon and a gold wax seal sticker.",
                "price": Decimal("12.99"),
                "stock": 25,
                "image_url": "https://images.unsplash.com/photo-1520854221256-17451cc331bf?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_alice,
                "category": categories["Wedding & Anniversary"],
                "title": "Minimalist Silver Foil Anniversary Card",
                "description": "Sleek and romantic typography in metallic silver foil against matte slate navy cardstock.",
                "price": Decimal("8.50"),
                "stock": 40,
                "image_url": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_john,
                "category": categories["Thank You & Gratitude"],
                "title": "Heartfelt Thanks Minimalist Card Pack (Set of 6)",
                "description": "A pack of 6 luxury thank you cards with kraft envelopes and gold foil stamped gratitude seal.",
                "price": Decimal("16.00"),
                "stock": 18,
                "image_url": "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_alice,
                "category": categories["Holiday & Seasonal"],
                "title": "Winter Wonderland Embossed Holiday Card",
                "description": "Silver and frost-embossed pine trees on recycled snowy white linen cardstock. Blank inside for personalized greetings.",
                "price": Decimal("6.25"),
                "stock": 50,
                "image_url": "https://images.unsplash.com/photo-1512909006721-3d6018887383?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_john,
                "category": categories["Luxury Gift Sets"],
                "title": "Artisan Wax Seal & Calligraphy Gift Card Box",
                "description": "Collector gift set including 4 handmade cards, solid brass wax seal stamp, burgundy sealing wax beads, and melting spoon.",
                "price": Decimal("34.99"),
                "stock": 12,
                "image_url": "https://images.unsplash.com/photo-1607344645866-009c320c5ab8?w=700&auto=format&fit=crop&q=80",
            },
            {
                "seller": seller_alice,
                "category": categories["Luxury Gift Sets"],
                "title": "Bliss Signature Keepsake Greeting Box",
                "description": "Deluxe magnetic-closure gift box containing 8 artisan seasonal cards, velvet envelopes, and gold ink pen.",
                "price": Decimal("45.00"),
                "stock": 8,
                "image_url": "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=700&auto=format&fit=crop&q=80",
            },
        ]

        for p_data in products_data:
            prod, created = Product.objects.get_or_create(
                title=p_data["title"],
                seller=p_data["seller"],
                defaults=p_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {prod.title} (${prod.price})"))
            else:
                self.stdout.write(f"Product exists: {prod.title}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))

