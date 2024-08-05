from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views


urlpatterns=[
    path('Registration/',views.Registration,name='Reg'),
    path('', views.Registration,name='Reg'),
    path('register/user/', views.UserRegistration, name='user_registration'),
    path('stateentry/',views.stateentry,name='stateentry'),
    path('address_entry/<int:state_id>/',views.addressentry,name='address_entry'),
    path('send-otp-email/', views.send_otp_email, name='send_otp_email'),
    path('seller-send-otp-email/', views.seller_send_otp_email, name='seller_send_otp_email'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('verify-otp-seller/', views.verify_otp_seller, name='verify_otp_seller'),
    path('Login/', views.Login, name='Login'), 
    path('logout/', views.auth_logout, name='logout'),
    path('home/',views.home,name='home'),
    path('update_roles/', views.update_roles, name='update_roles'),

    path('password_reset/',auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'),name="password_reset"),
    path('password_reset_done/',auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_sent.html'
    ),name="password_reset_done"),
    path('password_reset_confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ),name="password_reset_confirm"),
    path('password_reset_complete/',auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ),name="password_reset_complete"),
    path('ajax/load-states/', views.load_states, name='ajax_load_states'),
    path('profile_edit',views.profile_update,name="profile_edit"),
    path('Seller_login',views.SellerProfile,name="seller_login"),
    path('SellerReg',views.SellerRegister,name="SellerReg"),
    path('SellerHome',views.SellerProfile,name="SellerHome"),
    path('SellerDetails/<int:state_id>',views.Seller_Details,name="SellerDetails"),
    path('customer-dashboard/', views.customer_dashboard_with_seller_link, name='customer_dashboard_with_seller_link'),

    

]