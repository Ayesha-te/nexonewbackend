from django.urls import path

from .views import AdminWithdrawalsView, MyWithdrawalsView

urlpatterns = [
    path("me/", MyWithdrawalsView.as_view()),
    path("admin/", AdminWithdrawalsView.as_view()),
]
