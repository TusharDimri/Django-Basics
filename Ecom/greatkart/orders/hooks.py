from django.http import HttpResponse
from django.shortcuts import redirect, render
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.dispatch import receiver
import logging
from accounts.models import Account
from .models import Order, Payment, OrderProduct
from carts.models import CartItem
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.dispatch import Signal

payment_processed = Signal()

logger = logging.getLogger(__name__)

@csrf_exempt
@receiver(valid_ipn_received)
def paypal_ipn(sender, **kwargs):
    print("Order Successful")
    ipn_data = sender
    logger.info("Received IPN data")
    # print(ipn_data)
    # Process the IPN data
    if ipn_data.payment_status == ST_PP_COMPLETED:
        # Verify payment details (e.g., receiver email, amount)
        if ipn_data.receiver_email == settings.PAYPAL_RECEIVER_EMAIL:
            # print("Correct Email")
            transaction_id = ipn_data.txn_id
            order_number= ipn_data.item_number
            status = ipn_data.payment_status
            current_user = ipn_data.custom

            # print(transaction_id, order_number, status, current_user)


            user = Account.objects.get(email=current_user)
            order = Order.objects.get(user=user.id, is_ordered=False, order_number=order_number)
            if order:
                # Store transaction details inside Payment model:
                payment = Payment(
                    user=user,
                    payment_id=transaction_id,
                    payment_method='Paypal',
                    amount_paid=order.order_total,
                    status=status,
                )
                payment.save()
                order.payment = payment
                order.is_ordered = True
                order.save()


                #  Move Cart Items to OrderProducts table:
                cart_items = CartItem.objects.filter(user=user)

                for item in cart_items:
                    orderproduct = OrderProduct()
                    orderproduct.order_id = order.id
                    orderproduct.payment = payment
                    orderproduct.user_id = user.id
                    orderproduct.product_id = item.product_id
                    orderproduct.quantity = item.quantity
                    orderproduct.product_price = item.product.price
                    orderproduct.ordered = True
                    orderproduct.save()

                    cart_item = CartItem.objects.get(id=item.id)
                    product_variation = cart_item.variations.all()
                    orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                    orderproduct.variations.set(product_variation)
                    orderproduct.save()

                    # Reduce the quantity of the sold products
                    product = Product.objects.get(id=item.product_id)
                    product.stock -= item.quantity
                    product.save()

                # Clear cart
                CartItem.objects.filter(user=user).delete()

                print("DB updated with successful payment details")

                # Send order received email to customer
                # mail_subject = 'Thank you for your order!'
                # message = render_to_string('orders/order_recieved_email.html', {
                #     'user': user,
                #     'order': order,
                # })
                # to_email = user.email
                # send_email = EmailMessage(mail_subject, message, to=[to_email])
                # send_email.send()
                # return HttpResponse("OK")

            
        else:
            print("Invalid receiver email")
    else:
        print(f"Payment not completed: {ipn_data.payment_status}")

    # url = reverse('payment-success', kwargs={'order_number': order_number})
    # return redirect(url)
