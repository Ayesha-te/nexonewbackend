from django.urls import path

from .views import AdminApproveWithdrawalView, AdminWithdrawalsView, MyWithdrawalsView

urlpatterns = [
    path("me/", MyWithdrawalsView.as_view()),
    path("admin/", AdminWithdrawalsView.as_view()),
    path("admin/<int:pk>/approve/", AdminApproveWithdrawalView.as_view()),
]
