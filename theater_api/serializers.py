from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import StringRelatedField

from theater_api.models import (
    Genre,
    Actor,
    Play,
    TheaterHall,
    Performance,
    Reservation,
    Ticket,
)
from user.serializers import UserSerializer


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name"]


class TheaterHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheaterHall
        fields = ["id", "name", "rows", "seats_in_row"]


class PlayListSerializer(serializers.ModelSerializer):
    actor_list = serializers.StringRelatedField(
        many=True, read_only=True, source="actors"
    )
    genre_list = serializers.StringRelatedField(
        many=True, read_only=True, source="genres"
    )
    actors = serializers.SlugRelatedField(
        many=True, queryset=Actor.objects.all(), write_only=True, slug_field="id"
    )
    genres = serializers.SlugRelatedField(
        many=True, queryset=Genre.objects.all(), write_only=True, slug_field="name"
    )

    class Meta:
        model = Play
        fields = [
            "id",
            "title",
            "description",
            "actors",
            "genres",
            "actor_list",
            "genre_list",
        ]


class PlayDetailSerializer(serializers.ModelSerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ["id", "title", "description", "actors", "genres"]


class PerformanceListSerializer(serializers.ModelSerializer):
    play = serializers.SlugRelatedField(queryset=Play.objects.all(), slug_field="title")
    theater_hall = serializers.SlugRelatedField(
        queryset=TheaterHall.objects.all(), slug_field="name"
    )

    class Meta:
        model = Performance
        fields = ["id", "play", "theater_hall", "show_time"]


class PerformanceDetailSerializer(serializers.ModelSerializer):
    play = PlayDetailSerializer(many=False, read_only=True)
    theater_hall = TheaterHallSerializer(many=False, read_only=True)

    class Meta:
        model = Performance
        fields = ["id", "play", "theater_hall", "show_time"]


class TicketSerializer(serializers.ModelSerializer):
    play = serializers.CharField(source="performance.play.title", read_only=True)
    hall = serializers.CharField(source="performance.theater_hall.name", read_only=True)
    show_time = serializers.DateTimeField(
        source="performance.show_time", format="%Y-%m-%d %H:%M", read_only=True
    )

    class Meta:
        model = Ticket
        fields = ["row", "seat", "play", "hall", "show_time"]

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["performance"].theater_hall,
            ValidationError,
        )
        return data


class TicketDetailSerializer(TicketSerializer):
    play = PlayDetailSerializer(many=False, read_only=True, source="performance.play")
    hall = TheaterHallSerializer(
        many=False, read_only=True, source="performance.theater_hall"
    )

    class Meta:
        model = Ticket
        fields = ["row", "seat", "play", "hall", "show_time"]


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.email", read_only=True)
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket in tickets:
                Ticket.objects.create(reservation=reservation, **ticket)
            return reservation

    class Meta:
        model = Reservation
        fields = ["id", "created_at", "user", "tickets"]
        read_only_fields = ["created_at"]
