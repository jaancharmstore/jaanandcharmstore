from django.urls import path
from . import views

urlpatterns = [
    path('store/', views.store, name="store"),
    path('store/<str:category>/', views.store, name="store_search"),
    path('checkout/', views.checkout, name="checkout"),
    path('cart/', views.cart, name="cart"),
    path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),
    path('', views.landingPage, name="landing_page"),
    path('login/', views.login, name="login"),
    path('register/', views.register, name="register"),
    path('logout/', views.logout, name="logout"),
    path('shop/', views.shop, name="shop"),
    path('about/', views.about, name="about"),
    path('add-to-cart/', views.add_to_cart, name="add-to-cart"),
    path('get-cart/', views.get_cart, name="get-cart"),
    path('remove-cart/', views.remove_cart, name="remove-cart"),
    path('check-login/', views.check_login, name="check-login"),
    path('history/', views.history, name="history"),
    path('refund/', views.refund, name="refund"),
    path('detail/<int:product_id>', views.detailProduct, name='detail'),
]
