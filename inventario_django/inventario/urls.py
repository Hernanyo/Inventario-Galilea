#inventario_django/inventario/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from django.contrib.auth import views as auth_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/",  auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="productos:company_select"), name="logout"),
    #path("", include("productos.urls", namespace="productos")),
    path("", include(("productos.urls", "productos"), namespace="productos")),
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="accounts/recuperar_contraseña/password_reset.html"),name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/recuperar_contraseña/password_reset_done.html"),name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="accounts/recuperar_contraseña/password_reset_confirm.html"),name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/recuperar_contraseña/password_reset_complete.html"),name="password_reset_complete"),
]
