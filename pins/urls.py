from django.urls import path

from .views import AdminPinRequestView, MyPinsView, PinRequestView

urlpatterns = [
    path("me/", MyPinsView.as_view()),
    path("requests/", PinRequestView.as_view()),
    path("admin/requests/", AdminPinRequestView.as_view()),
    path("admin/requests/<int:pk>/", AdminPinRequestView.as_view()),
]
