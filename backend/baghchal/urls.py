from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_game),
    path("join/", views.join_game),
    path("rejoin/", views.rejoin_game),
    path("quick-match/", views.quick_match),
]