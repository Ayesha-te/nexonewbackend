from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_tree_payload


class MyTreeApiView(APIView):
    def get(self, request):
        return Response(build_tree_payload(request.user))
