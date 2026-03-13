from django.urls import path

from .views import (
    ActivateUserView,
    AdminDashboardView,
    AdminSystemStatusView,
    AdminUserDetailView,
    AdminUsersView,
    ChangePasswordView,
    MeView,
    MyTreeView,
    SignupView,
)

urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("me/", MeView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("activate/", ActivateUserView.as_view()),
    path("tree/", MyTreeView.as_view()),
    path("admin/dashboard/", AdminDashboardView.as_view()),
    path("admin/system-status/", AdminSystemStatusView.as_view()),
    path("admin/users/", AdminUsersView.as_view()),
    path("admin/users/<int:pk>/", AdminUserDetailView.as_view()),
]
