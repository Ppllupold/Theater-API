from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils.timezone import now
from datetime import timedelta

from theater_api.models import (
    Reservation,
    Ticket,
    TheaterHall,
    Play,
    Performance,
    Genre,
    Actor,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseReservationTestMixin:
    def create_user(self, is_staff=False):
        return User.objects.create_user(
            email="admin@example.com" if is_staff else "user@example.com",
            password="testpass123",
            is_staff=is_staff,
        )

    def create_genre(self, name="Drama"):
        return Genre.objects.create(name=name)

    def create_actor(self, first_name="Tom", last_name="Hanks"):
        return Actor.objects.create(first_name=first_name, last_name=last_name)

    def create_play(self):
        genre = self.create_genre()
        actor = self.create_actor()
        play = Play.objects.create(title="Hamlet", description="Classic tragedy")
        play.genres.add(genre)
        play.actors.add(actor)
        return play

    def create_hall(self):
        return TheaterHall.objects.create(name="Main Hall", rows=10, seats_in_row=10)

    def create_performance(self):
        return Performance.objects.create(
            play=self.create_play(),
            theater_hall=self.create_hall(),
            show_time=now() + timedelta(days=3),
        )


class TestReservation(BaseReservationTestMixin, APITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.client.force_authenticate(self.user)
        self.performance = self.create_performance()

    def test_user_must_be_authenticated(self):
        self.client.logout()
        url = reverse("reservation-list")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reservation_created_with_authenticated_user(self):
        url = reverse("reservation-list")
        payload = {
            "tickets": [{"row": 1, "seat": 1, "performance": self.performance.id}]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.user, self.user)

    def test_ticket_created_with_reservation(self):
        url = reverse("reservation-list")
        payload = {
            "tickets": [{"row": 5, "seat": 7, "performance": self.performance.id}]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reservation_id = response.data["id"]
        self.assertTrue(Ticket.objects.filter(reservation=reservation_id).exists())
