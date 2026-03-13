from django.urls import path

from .views import MyLedgerView, MyWalletView

urlpatterns = [
    path("me/", MyWalletView.as_view()),
    path("entries/", MyLedgerView.as_view()),
]
