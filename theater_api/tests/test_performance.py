import datetime
from django.utils.timezone import now
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from theater_api.models import (
    Performance,
    TheaterHall,
    Play,
    Reservation,
    Ticket,
    Genre,
    Actor,
)

User = get_user_model()


class BaseTestSetupMixin:
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
        play = Play.objects.create(title="Hamlet", description="Tragedy")
        play.genres.add(genre)
        play.actors.add(actor)
        return play

    def create_theater_hall(self):
        return TheaterHall.objects.create(name="Main Hall", rows=5, seats_in_row=5)

    def create_performance(self):
        return Performance.objects.create(
            play=self.create_play(),
            theater_hall=self.create_theater_hall(),
            show_time=now() + datetime.timedelta(days=1),
        )


class AuthenticatedPerformancePublicTests(BaseTestSetupMixin, APITestCase):
    def setUp(self):
        self.user = self.create_user()
        self.client.force_authenticate(self.user)
        self.performance = self.create_performance()

    def test_list_performances(self):
        url = reverse("performance-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_available_tickets_endpoint(self):
        url = reverse("performance-available-tickets", args=[self.performance.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(res.data, list))
        self.assertTrue({"row", "seat"} <= res.data[0].keys())
        self.assertEqual(
            len(res.data),
            self.performance.theater_hall.rows
            * self.performance.theater_hall.seats_in_row,
        )
