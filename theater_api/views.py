from datetime import timedelta

from django.db.models import Count, Q, F
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework_extensions.mixins import DetailSerializerMixin

from theater_api.models import (
    Genre,
    Actor,
    Play,
    TheaterHall,
    Performance,
    Reservation,
    Ticket,
)
from theater_api.permissions import IsAdminAllOrReadOnly
from theater_api.serializers import (
    GenreSerializer,
    ActorSerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    TheaterHallSerializer,
    PerformanceListSerializer,
    PerformanceDetailSerializer,
    ReservationSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAuthenticated, IsAdminAllOrReadOnly)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("first_name")
    serializer_class = ActorSerializer
    permission_classes = (IsAuthenticated, IsAdminAllOrReadOnly)


class TheaterHallViewSet(viewsets.ModelViewSet):
    queryset = TheaterHall.objects.all()
    serializer_class = TheaterHallSerializer
    permission_classes = (IsAuthenticated, IsAdminAllOrReadOnly)


class PlayViewSet(DetailSerializerMixin, viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_detail_class = PlayDetailSerializer
    serializer_class = PlayListSerializer
    permission_classes = (IsAuthenticated, IsAdminAllOrReadOnly)

    def get_queryset(self):
        genres = self.request.query_params.get("genres", None)
        if genres:
            genres = [g.strip() for g in genres.split(",") if g.strip()]
            for genre in genres:
                self.queryset = self.queryset.filter(genres__name__iexact=genre)
        return self.queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="genres",
                type=str,
                location="query",
                description="comma separated genre names. Result includes instances that necessarily have all the genres from request",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = {
            "week_most_popular": self.get_week_most_popular_name(),
            "results": response.data,
        }
        return response

    @staticmethod
    def get_week_most_popular_name() -> dict:
        seven_days_ago = timezone.now() - timedelta(days=7)
        return (
            Play.objects.annotate(
                last_week_tickets=Count(
                    "performances__tickets",
                    filter=Q(performances__show_time__gte=seven_days_ago),
                )
            )
            .order_by("-last_week_tickets")
            .values("id", "title")
            .first()
        )


class PerformanceViewSet(viewsets.ModelViewSet, DetailSerializerMixin):
    queryset = Performance.objects.select_related(
        "play", "theater_hall"
    ).prefetch_related("tickets")
    serializer_class = PerformanceListSerializer
    serializer_detail_class = PerformanceDetailSerializer
    permission_classes = (IsAuthenticated, IsAdminAllOrReadOnly)

    @action(
        detail=True,
        methods=["get"],
        url_path="available-tickets",
        permission_classes=(IsAuthenticated,),
    )
    def available_tickets(self, request, pk=None):
        performance = self.get_object()
        hall = performance.theater_hall
        row_filter = request.query_params.get("row")

        try:
            row_filter = int(row_filter) if row_filter else None
        except ValueError:
            return Response({"error": "Row must be an integer."}, status=400)

        if row_filter:
            if not (1 <= row_filter <= hall.rows):
                return Response(
                    {"error": f"Row must be in range 1 to {hall.rows}."}, status=400
                )
            rows = [row_filter]
        else:
            rows = range(1, hall.rows + 1)

        all_seats = [
            {"row": row, "seat": seat}
            for row in rows
            for seat in range(1, hall.seats_in_row + 1)
        ]

        booked = set(
            Ticket.objects.filter(performance=performance).values_list("row", "seat")
        )

        available = [
            seat for seat in all_seats if (seat["row"], seat["seat"]) not in booked
        ]

        return Response(available)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related("user")
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
