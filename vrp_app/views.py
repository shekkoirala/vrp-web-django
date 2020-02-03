from django.http import QueryDict
from rest_framework import viewsets
from rest_framework.response import Response
import pandas
from django.views.generic import View
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse


from vrp_app.serializers import VRPSerializer


class VRPAPI(viewsets.ViewSet):
    # permission_classes = (IsAuthenticated, )
    serializer_class = VRPSerializer

    def create(self, request):
        data = request.data.dict() if isinstance(request.data, QueryDict) else request.data
        serializer = self.serializer_class(data=data)
        cleaned_data = serializer.clean(data)
        parsed_data = serializer.parse(cleaned_data)
        return Response(parsed_data)

    def write_down(self, request):
        data = request.data.dict() if isinstance(request.data, QueryDict) else request.data
        serializer = self.serializer_class(data=data)
        cleaned_data = serializer.clean(data)
        parsed_data = serializer.parse(cleaned_data)
        df = pandas.DataFrame(parsed_data)
        df.to_csv("./file2.csv", sep=',',index=False)

        return None



   






