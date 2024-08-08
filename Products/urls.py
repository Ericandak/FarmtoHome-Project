from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('add/', views.add_product, name='add_product'),
    path('seller-home/', views.seller_home, name='seller_home'),
    path('sellerproductlist/',views.productlist,name="sellerproductlist"),
    path('productedit/<int:product_id>/',views.productedit,name="productedit"),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name="add_to_cart"),
    path('usercart/',views.cartview,name="usercart"),
    path('update_cart_item/',views.update_cart_item,name="update_cart_item"),
    path('delete_cart',views.deletecart,name="delete_cart"),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search_results, name='search_results'),
]