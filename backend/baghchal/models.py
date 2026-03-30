from django.db import models

from core.models import User


class Game(models.Model):
    WINNER_ROLE_CHOICES = [("goat", "Goat"), ("tiger", "Tiger")]
    END_REASON_CHOICES = [
        ("goats_captured", "5 Goats Captured"),
        ("tigers_blocked", "All Tigers Blocked"),
    ]

    game_id = models.CharField(primary_key=True, max_length=8, unique=True)

    goat_player = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="games_as_goat"
    )
    tiger_player = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="games_as_tiger"
    )

    # Role that won, not a FK — derive the winning user via goat_player/tiger_player
    winner_role = models.CharField(max_length=5, choices=WINNER_ROLE_CHOICES, null=True)
    end_reason = models.CharField(max_length=20, choices=END_REASON_CHOICES, null=True)

    total_moves = models.IntegerField(default=0)
    goats_captured = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def winning_player(self):
        if self.winner_role == "goat":
            return self.goat_player
        elif self.winner_role == "tiger":
            return self.tiger_player
        return None

    def losing_player(self):
        if self.winner_role == "goat":
            return self.tiger_player
        elif self.winner_role == "tiger":
            return self.goat_player
        return None

    def __str__(self):
        return f"Game {self.game_id} | {self.winner_role} won ({self.end_reason})"