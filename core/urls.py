from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.auth import EmailTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", EmailTokenObtainPairView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/accounts/", include("accounts.urls")),
    path("api/pins/", include("pins.urls")),
    path("api/network/", include("network.urls")),
    path("api/wallets/", include("wallets.urls")),
    path("api/withdrawals/", include("withdrawals.urls")),
    path("api/rewards/", include("rewards.urls")),
    path("api/complaints/", include("complaints.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/ads/", include("ads.urls")),
    path("api/attendance/", include("attendance.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
