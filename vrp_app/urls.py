from django.urls import path
from django.conf.urls import url 

from rest_framework import routers

from vrp_app.views import VRPAPI


urlpatterns = list()

router = routers.DefaultRouter()

router.register(r"parse", VRPAPI, base_name='VRP-parser')

urlpatterns += router.urls


