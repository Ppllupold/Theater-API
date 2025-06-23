from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint
from rest_framework.exceptions import ValidationError


class Genre(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name}"


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    genres = models.ManyToManyField(Genre, related_name="plays", blank=True)
    actors = models.ManyToManyField(Actor, related_name="plays", blank=True)

    def __str__(self):
        return self.title


class TheaterHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Performance(models.Model):
    play = models.ForeignKey(
        Play, on_delete=models.CASCADE, related_name="performances"
    )
    theater_hall = models.ForeignKey(
        TheaterHall, on_delete=models.CASCADE, related_name="performances"
    )
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.play.title} @ {self.show_time}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="reservations"
    )

    def __str__(self):
        return f"Reservation {self.id} by {self.user}"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    performance = models.ForeignKey(
        Performance, on_delete=models.CASCADE, related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="tickets"
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["row", "seat", "performance"],
                name="unique_ticket_fields_together",
            ),
        ]

    def __str__(self):
        return f"Ticket {self.id} for seat {self.row}-{self.seat}"

    @staticmethod
    def validate_ticket(row: int, seat: int, cinema_hall, error_to_raise):
        if not (1 <= row <= cinema_hall.rows):
            raise error_to_raise(
                {"row": f"Row number must be in range 1 to {cinema_hall.rows}."}
            )

        if not (1 <= seat <= cinema_hall.seats_in_row):
            raise error_to_raise(
                {
                    "seat": f"Seat number must be in range 1 to {cinema_hall.seats_in_row}."
                }
            )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.performance.theater_hall,
            ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
