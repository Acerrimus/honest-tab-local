import reflex as rx
import stripe
import qrcode
import io
import base64
from typing import List

# Import your existing Order class
from .order import Order 

# --- CONFIGURATION ---
stripe.api_key = "sk_test_YOUR_KEY_HERE"

class PaymentState(rx.State):
    qr_code: str = ""
    is_loading: bool = False
    
    # This represents the user's current "bill" or "cart"
    # You will populate this list from your main application logic
    current_orders: List[Order] = [] 

    @rx.var
    def total_display(self) -> str:
        """Calculates the total for the UI (e.g., '€45.50')"""
        total = sum(o.price * o.quantity for o in self.current_orders)
        return f"€{total:.2f}"

    def generate_dynamic_qr(self):
        """Generates a QR code based on the items in current_orders."""
        
        # 1. Validation: Don't generate if empty
        if not self.current_orders:
            print("No orders to pay for.")
            return

        self.is_loading = True
        yield

        try:
            # 2. Convert your 'Order' objects to Stripe 'Line Items'
            stripe_line_items = []
            
            for order in self.current_orders:
                # IMPORTANT: Stripe wants integer CENTS (e.g., 10.00 -> 1000)
                # We round to avoid floating point errors (14.99999 -> 15)
                unit_amount_cents = int(round(order.price * 100))
                
                # Stripe requires quantity as an integer
                qty_int = int(order.quantity)
                
                # Skip invalid items
                if unit_amount_cents <= 0 or qty_int <= 0:
                    continue

                stripe_line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': order.item, # Uses the 'item' string from your Order class
                            # Optional: Add description if you want
                            # 'description': order.comment 
                        },
                        'unit_amount': unit_amount_cents,
                    },
                    'quantity': qty_int,
                })

            # 3. Create the Stripe Session
            session = stripe.checkout.Session.create(
                line_items=stripe_line_items,
                mode='payment',
                success_url='https://your-domain.com/success', # Can be a dummy URL for now
                automatic_payment_methods={'enabled': True}, # Enables Bizum/Apple Pay based on settings
            )

            # 4. Generate QR Image
            img = qrcode.make(session.url)
            buff = io.BytesIO()
            img.save(buff, format="PNG")
            img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
            self.qr_code = f"data:image/png;base64,{img_str}"

        except Exception as e:
            print(f"Stripe Error: {e}")
            # Optional: self.error_message = str(e)
        
        self.is_loading = False