from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

class Home(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        content = {'message': 'Welcome to the capstone_project API home route!'}
        return Response(content)
