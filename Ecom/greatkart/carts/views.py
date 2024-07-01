from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from store.models import Variation
from django.contrib.auth.decorators import login_required

# Create your views here.
def _cart_id(request): # Private Function
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id) # Get the Product

    #  if the user is authenticated:
    if current_user.is_authenticated:
        product_variation = []
        # Get The Product Variation
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except Exception as e:
                    pass
        
        cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if cart_item_exists :
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            # existing_variations (coming from database)
            # Current Variation (coming from prodict_variation)
            # item_id (coming from database)
            existing_variations = []
            id = []
            for item in cart_item:
                ex_variations  = item.variations.all()
                existing_variations.append(list(ex_variations))
                id.append(item.id)

            if product_variation in existing_variations:
                #  Increase the Cart Item Quantity
                index = existing_variations.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity+=1
                item.save()

            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear() 
                    item.variations.add(*product_variation)
                item.save()      
        
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                user=current_user,
            ) 
            if len(product_variation) > 0:
                cart_item.variations.clear() 
                cart_item.variations.add(*product_variation)
            cart_item.save()
   
        return redirect('cart')

    # if the user is not authenticated:
    else:
        product_variation = []
        # Get The Product Variation
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except Exception as e:
                    pass
        try:
            # Get the cart using the cart_id present in the session
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()

        cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if cart_item_exists :
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            # existing_variations (coming from database)
            # Current Variation (coming from prodict_variation)
            # item_id (coming from database)
            existing_variations = []
            id = []
            for item in cart_item:
                ex_variations  = item.variations.all()
                existing_variations.append(list(ex_variations))
                id.append(item.id)

            if product_variation in existing_variations:
                #  Increase the Cart Item Quantity
                index = existing_variations.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity+=1
                item.save()

            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear() 
                    item.variations.add(*product_variation)
                item.save()      
        
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart,
            ) 
            if len(product_variation) > 0:
                cart_item.variations.clear() 
                cart_item.variations.add(*product_variation)
            cart_item.save()
   
        return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=0):
    try:
        tax=0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity = cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist: 
        pass # ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


def remove_cart(request, product_id, cart_item_id):
    
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)    
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item.delete()
    except Exception as e:
        pass   
    
    return redirect("cart")

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)    
        cart_item.delete()
    else:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    return redirect("cart")

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=0):
    try:
        tax=0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity = cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist: 
        pass # ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context=context)