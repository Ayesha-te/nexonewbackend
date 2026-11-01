from django.db.models import Count, Q, Sum
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RewardTier, UserReward
from .serializers import AdminUserRewardSerializer, RewardTierSerializer, UserRewardSerializer


class RewardPlanView(APIView):
    permission_classes = []

    def get(self, request):
        return Response(RewardTierSerializer(RewardTier.objects.all().order_by("sequence"), many=True).data)


class MyRewardsView(APIView):
    def get(self, request):
        return Response(UserRewardSerializer(request.user.rewards.all().order_by("tier__sequence"), many=True).data)


class AdminRewardHistoryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rows = UserReward.objects.select_related("user", "tier").order_by("-rewarded_at")

        user_id = request.query_params.get("userId")
        if user_id:
            rows = rows.filter(user_id=user_id)

        search = request.query_params.get("search")
        if search:
            rows = rows.filter(
                Q(user__email__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        level = request.query_params.get("level")
        if level:
            rows = rows.filter(tier__sequence=level)

        date_from = request.query_params.get("from")
        if date_from:
            rows = rows.filter(rewarded_at__date__gte=date_from)

        date_to = request.query_params.get("to")
        if date_to:
            rows = rows.filter(rewarded_at__date__lte=date_to)

        return Response(AdminUserRewardSerializer(rows[:1000], many=True).data)


class AdminRewardSummaryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        paid_rewards = UserReward.objects.filter(amount__gt=0)
        total_amount = paid_rewards.aggregate(total=Sum("amount"))["total"] or 0
        total_transactions = paid_rewards.count()

        by_milestone = (
            UserReward.objects.values("tier__sequence", "tier__reward")
            .annotate(count=Count("id"), total_amount=Sum("amount"))
            .order_by("tier__sequence")
        )

        top_users = (
            paid_rewards.values("user_id", "user__email", "user__username")
            .annotate(total_amount=Sum("amount"), count=Count("id"))
            .order_by("-total_amount")[:50]
        )

        return Response(
            {
                "totalRewardsDistributed": total_amount,
                "totalTransactions": total_transactions,
                "byMilestone": [
                    {
                        "level": row["tier__sequence"],
                        "milestone": row["tier__reward"],
                        "count": row["count"],
                        "totalAmount": row["total_amount"] or 0,
                    }
                    for row in by_milestone
                ],
                "topUsers": [
                    {
                        "userId": row["user_id"],
                        "email": row["user__email"],
                        "username": row["user__username"],
                        "totalAmount": row["total_amount"] or 0,
                        "count": row["count"],
                    }
                    for row in top_users
                ],
            }
        )
