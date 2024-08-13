from django.urls import path
from . import views, hooks

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('place_order/payment-success/<order_number>/', views.PaymentSuccessful, name='payment-success'),
    path('place_order/payment-failed/<order_number>/', views.paymentFailed, name='payment-failed'),
    path('paypal-ipn/', hooks.paypal_ipn, name='paypal-ipn'),
    path('check-order-status/<str:order_number>/', views.check_order_status, name='check_order_status'),
]
