from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from theater_api.models import Play, Genre, Actor
from django.contrib.auth import get_user_model

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


class AuthenticatedPlayTests(BaseTestSetupMixin, APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=self.create_user())

    def test_list_plays(self):
        self.create_play()
        url = reverse("play-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertIn("week_most_popular", res.data)

    def test_play_detail(self):
        play = self.create_play()
        url = reverse("play-detail", args=[play.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Hamlet")

    def test_filter_by_single_genre(self):
        drama = self.create_genre("Drama")
        tragedy = self.create_genre("Tragedy")
        play1 = Play.objects.create(title="Hamlet", description="Classic tragedy")
        play1.genres.set([drama, tragedy])
        play1.actors.add(self.create_actor())

        play2 = Play.objects.create(title="Othello", description="Drama only")
        play2.genres.set([drama])
        play2.actors.add(self.create_actor(first_name="O", last_name="Tello"))

        url = reverse("play-list") + "?genres=Drama"
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_titles = [p["title"] for p in res.data["results"]]
        self.assertIn("Hamlet", returned_titles)
        self.assertIn("Othello", returned_titles)

    def test_filter_by_multiple_genres(self):
        drama = self.create_genre("Drama")
        tragedy = self.create_genre("Tragedy")
        comedy = self.create_genre("Comedy")

        play1 = Play.objects.create(title="Hamlet")
        play1.genres.set([drama, tragedy])
        play1.actors.add(self.create_actor(first_name="W", last_name="Spear"))

        play2 = Play.objects.create(title="Twelfth Night")
        play2.genres.set([comedy])
        play2.actors.add(self.create_actor(first_name="T", last_name="Night"))

        play3 = Play.objects.create(title="Othello")
        play3.genres.set([drama])
        play3.actors.add(self.create_actor(first_name="O", last_name="Tello"))

        url = reverse("play-list") + "?genres=Drama,Tragedy"
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_titles = [p["title"] for p in res.data["results"]]
        self.assertIn("Hamlet", returned_titles)
        self.assertNotIn("Twelfth Night", returned_titles)
        self.assertNotIn("Othello", returned_titles)

    def test_filter_by_nonexistent_genre(self):
        self.create_play()
        url = reverse("play-list") + "?genres=Fantasy"
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 0)
