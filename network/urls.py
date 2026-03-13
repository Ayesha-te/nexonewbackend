from django.urls import path

from .views import MyTreeApiView

urlpatterns = [path("tree/", MyTreeApiView.as_view())]
