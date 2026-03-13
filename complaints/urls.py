from django.urls import path

from .views import AdminComplaintFeedbackView, ComplaintFeedbackView

urlpatterns = [
    path("me/", ComplaintFeedbackView.as_view()),
    path("admin/", AdminComplaintFeedbackView.as_view()),
    path("admin/<int:pk>/", AdminComplaintFeedbackView.as_view()),
]
