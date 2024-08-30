import logging
from django.shortcuts import render, redirect, HttpResponse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
import datetime 
from django.views.decorators.csrf import csrf_exempt


from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid
from django.urls import reverse


import logging
import time
from django.http import JsonResponse



def payments(request):
    return render(request, 'orders/payments.html')

def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is <= 0, redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate Order Number
            current_date = datetime.datetime.now().strftime('%Y%m%d')  # Format: 20240610
            order_number = f"{current_date}{data.id}"  # Format: 20240610id
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            # Generate item names from cart items
            item_names = [item.product.product_name for item in cart_items]
            item_name_str = ', '.join(item_names)


            host = request.get_host()

            paypal_checkout = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': total+tax,
                'custom':current_user, 
                'currency_code': 'USD',
                'item_name': item_name_str,
                'invoice': str(uuid.uuid4()),
                "item_number":order_number,
                'notify_url': f"https://bb23-2405-201-680a-b07c-a482-6c31-7d21-4b2e.ngrok-free.app{reverse('paypal-ipn')}",
                'return_url': f"http://{host}{reverse('payment-success', kwargs = {'order_number': order_number})}",
                'cancel_url': f"http://{host}{reverse('payment-failed', kwargs = {'order_number': order_number})}",

                
            }

            paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)

            context = {
                'order':order,
                'cart_items':cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'paypal': paypal_payment,
            }
                       

            return render(request, 'orders/payments.html', context)
        else:
            print(form.errors)
            return redirect('checkout')

    # If not a POST request, redirect back to the cart or home page
    return redirect('store')

def check_order_status(request, order_number):
    timeout = 30  # seconds to keep the request open
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            order = Order.objects.get(order_number=order_number)
            if order.is_ordered:
                return JsonResponse({'is_ordered': True})
        except Order.DoesNotExist:
            pass
        
        time.sleep(1)  # Sleep for 1 second before checking again

    return JsonResponse({'is_ordered': False})

@csrf_exempt
def PaymentSuccessful(request, order_number):
    print(order_number)

    # return HttpResponse(f"Order {order_number} successful")

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        print('1 or 2')
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = order.payment  # Directly access the payment field of the order

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id if payment else None,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/payment_successful.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
            context = {
                'order_number':order_number
            }
            return render(request, 'orders/payment_processing.html', context=context)

def paymentFailed(request, order_number):

    # return HttpResponse(f"Order {order_number} failed")
    context = {
        order_number : order_number,
    }
    return render(request, 'orders/payment_successful.html', context)