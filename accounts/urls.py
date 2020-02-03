from django.urls import path

from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views

from .views import UserAuthenticate

router = routers.DefaultRouter()

urlpatterns = router.urls

urlpatterns += [
    path('authenticate/', UserAuthenticate.as_view(), name='obtain-token'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='refresh-token'),
]
