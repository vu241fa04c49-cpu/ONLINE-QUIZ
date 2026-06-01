from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("forgot-password/", views.forgot_password_page, name="forgot_password"),
    path("verify-otp/", views.verify_otp_page, name="verify_otp"),
    path("reset-password/", views.reset_password_page, name="reset_password"),
    path("logout/", views.logout_page, name="logout"),
]
