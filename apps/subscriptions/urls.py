from django.urls import path
from .views import (
    PlanListView, MySubscriptionView, VerifyPurchaseView, AppleServerNotificationView,
)

urlpatterns = [
    path('plans/',  PlanListView.as_view(),        name='plans'),
    path('mine/',   MySubscriptionView.as_view(),  name='my-subscription'),
    path('verify-purchase/',     VerifyPurchaseView.as_view(),          name='verify-purchase'),
    path('apple-notifications/', AppleServerNotificationView.as_view(), name='apple-notifications'),
]
