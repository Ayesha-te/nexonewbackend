from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RewardTier
from .serializers import RewardTierSerializer, UserRewardSerializer


class RewardPlanView(APIView):
    permission_classes = []

    def get(self, request):
        return Response(RewardTierSerializer(RewardTier.objects.all().order_by("sequence"), many=True).data)


class MyRewardsView(APIView):
    def get(self, request):
        return Response(UserRewardSerializer(request.user.rewards.all().order_by("tier__sequence"), many=True).data)
