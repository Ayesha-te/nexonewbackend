from django.urls import path

from .views import MyRewardsView, RewardPlanView

urlpatterns = [
    path("plan/", RewardPlanView.as_view()),
    path("me/", MyRewardsView.as_view()),
]
