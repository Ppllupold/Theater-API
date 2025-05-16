from django.urls import path, include
from rest_framework import routers

from theater_api.views import (
    GenreViewSet,
    ActorViewSet,
    PlayViewSet,
    TheaterHallViewSet,
    PerformanceViewSet,
    ReservationViewSet,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("plays", PlayViewSet)
router.register("theaterHalls", TheaterHallViewSet)
router.register("performances", PerformanceViewSet)
router.register("reservations", ReservationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
