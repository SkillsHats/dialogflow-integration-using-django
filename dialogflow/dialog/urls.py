from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home),
    # path('webhook/', views.webhook, name='webhook'),
    path('webhook/', views.new_webhook, name="newwebhook")
]