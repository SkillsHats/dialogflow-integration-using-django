from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home),
    path('location/', views.get_location),
    # path('webhook/', views.webhook, name='webhook'),
    path('webhook/', views.new_webhook, name="newwebhook")
]
