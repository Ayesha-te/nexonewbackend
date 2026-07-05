from django.urls import path

from .views import AdminPinRequestView, AdminPinSettingsView, MyPinsView, PinConfigView, PinRequestView

urlpatterns = [
    path("me/", MyPinsView.as_view()),
    path("config/", PinConfigView.as_view()),
    path("requests/", PinRequestView.as_view()),
    path("admin/settings/", AdminPinSettingsView.as_view()),
    path("admin/requests/", AdminPinRequestView.as_view()),
    path("admin/requests/<int:pk>/", AdminPinRequestView.as_view()),
]
