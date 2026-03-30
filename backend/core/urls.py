from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("signup/", views.signup),
    path("login/", views.login),
    path("guest-login/", views.guest_login),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("auth/google", views.google_auth),
    path("users/<str:username>/", views.user_stats)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
