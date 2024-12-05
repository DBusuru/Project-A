from decimal import Decimal
from shopease.models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            # save an empty cart in the session
            cart = self.session['cart'] = {}
        self.cart = cart
        print("Cart initialized with:", self.cart)  # Debug print

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0,
                                   'price': str(product.price),
                                   'product_id': product.id}
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        print("Added to cart:", self.cart)  # Debug print
        self.save()

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """
        Mark the session as modified to make sure it gets saved.
        """
        self.session.modified = True
        print("Cart saved:", self.cart)  # Debug print

    def __len__(self):
        """
        Count all items in the cart
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return float(sum(float(item['price']) * item['quantity'] for item in self.cart.values()))

    def clear(self):
        del self.session['cart']
        self.session.modified = True

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = self.cart.keys()
        print("Product IDs in cart:", list(product_ids))  # Debug print
        
        # Get the product objects
        products = Product.objects.filter(id__in=product_ids)
        
        cart = self.cart.copy()
        for product in products:
            product_id = str(product.id)
            if product_id in cart:
                cart[product_id].update({
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': str(product.price),
                        'image': str(product.image) if product.image else None
                    },
                    'product_id': product.id,  # Ensure product_id is always available
                    'total_price': float(cart[product_id]['price']) * cart[product_id]['quantity']
                })
        
        for item in cart.values():
            print("Yielding cart item:", item)  # Debug print
            yield item

    def to_json(self):
        """Return a JSON-serializable representation of the cart"""
        return {
            'items': [{
                'id': k,
                'quantity': v['quantity'],
                'price': str(v['price']),
                'name': v['name'],
                'image': v['image']
            } for k, v in self.cart.items()],
            'total_price': str(self.get_total_price())
        }
  