from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from theater_api.models import Genre, Actor, Play, TheaterHall

User = get_user_model()


class AuthPermissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", password="testpass123", is_staff=True
        )
        self.genre = Genre.objects.create(name="Drama")
        self.actor = Actor.objects.create(first_name="Tom", last_name="Hanks")
        self.theater_hall = TheaterHall.objects.create(
            name="Main Hall", rows=10, seats_in_row=10
        )
        self.play = Play.objects.create(title="Hamlet", description="Tragedy")
        self.play.genres.add(self.genre)
        self.play.actors.add(self.actor)

    def check_read_only_for_user(self, url):
        self.client.force_authenticate(self.user)
        res_get = self.client.get(url)
        self.assertIn(
            res_get.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        )
        res_post = self.client.post(url, {}, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    def check_write_allowed_for_admin(self, url, payload):
        self.client.force_authenticate(self.admin)
        res_post = self.client.post(url, payload, format="json")
        self.assertIn(
            res_post.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_genre_permissions(self):
        list_url = reverse("genre-list")
        detail_url = reverse("genre-detail", args=[self.genre.id])
        self.check_read_only_for_user(list_url)
        self.check_write_allowed_for_admin(list_url, {"name": "Comedy"})

        self.client.force_authenticate(self.admin)
        res_patch = self.client.patch(detail_url, {"name": "Updated"}, format="json")
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        res_delete = self.client.delete(detail_url)
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_actor_permissions(self):
        list_url = reverse("actor-list")
        detail_url = reverse("actor-detail", args=[self.actor.id])
        self.check_read_only_for_user(list_url)
        self.check_write_allowed_for_admin(
            list_url, {"first_name": "Brad", "last_name": "Pitt"}
        )

        self.client.force_authenticate(self.admin)
        res_patch = self.client.patch(
            detail_url, {"first_name": "Updated"}, format="json"
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        res_delete = self.client.delete(detail_url)
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_play_permissions(self):
        list_url = reverse("play-list")
        detail_url = reverse("play-detail", args=[self.play.id])
        self.check_read_only_for_user(list_url)
        self.check_write_allowed_for_admin(
            list_url,
            {
                "title": "New Play",
                "description": "desc",
                "genres": [self.genre.name],
                "actors": [self.actor.id],
            },
        )

        self.client.force_authenticate(self.admin)
        res_patch = self.client.patch(detail_url, {"title": "Updated"}, format="json")
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        res_delete = self.client.delete(detail_url)
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_theaterhall_permissions(self):
        list_url = reverse("theaterhall-list")
        detail_url = reverse("theaterhall-detail", args=[self.theater_hall.id])
        self.check_read_only_for_user(list_url)
        self.check_write_allowed_for_admin(
            list_url, {"name": "Small Hall", "rows": 5, "seats_in_row": 8}
        )

        self.client.force_authenticate(self.admin)
        res_patch = self.client.patch(
            detail_url, {"name": "Updated Hall"}, format="json"
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        res_delete = self.client.delete(detail_url)
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)
