from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'), 
    path('catalogue/', catalogue, name='catalogue'), 
    path('profile/<int:user_id>/', user_profile, name='profile'),
    path('add_product/', add_product, name='add_product'),
    path('product/update/<int:product_id>/', update_product, name='update_product'),
    path('product/delete/<int:product_id>/', delete_product, name='delete_product'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('paypal/cancelled/', payment_cancel, name='payment_cancel'),
    path('payment/<int:product_id>/', payment_view, name='payment'),
    path('payment/handle/', handle_payment, name='handle_payment'),
    path('payment/success/<int:order_id>/', success_view, name='payment_suc'),
    path('payment/invoice/<int:order_id>/', download_invoice, name='download_invoice'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('update-cart/', update_cart, name='update_cart'),
    path('remove-from-cart/', remove_from_cart, name='remove_from_cart'),
    
    path('create-order/', create_order, name='create_order'),
    path('payment-success/<int:order_id>/', payment_success, name='payment_success'),
    path('payment-cancelled/<int:order_id>/', payment_cancelled, name='payment_cancelled'),



]