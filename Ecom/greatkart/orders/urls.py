from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('place_order/payment-success/<order_number>/', views.PaymentSuccessful, name='payment-success'),
    path('place_order/payment-failed/<order_number>/', views.paymentFailed, name='payment-failed'),
]
