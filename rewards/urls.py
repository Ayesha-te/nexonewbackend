from django.urls import path

from .views import AdminRewardHistoryView, AdminRewardSummaryView, MyRewardsView, RewardPlanView

urlpatterns = [
    path("plan/", RewardPlanView.as_view()),
    path("me/", MyRewardsView.as_view()),
    path("admin/history/", AdminRewardHistoryView.as_view()),
    path("admin/summary/", AdminRewardSummaryView.as_view()),
]
