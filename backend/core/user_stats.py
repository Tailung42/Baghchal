from django.db.models import Q, Count, F
from baghchal.models import Game


def get_user_stats(user):
    games = Game.objects.filter(
        Q(goat_player=user) | Q(tiger_player=user)
    )

    games_played = games.count()
    wins = games.filter(
        Q(goat_player=user, winner_role="goat") |
        Q(tiger_player=user, winner_role="tiger")
    ).count()

    return {
        "games_played": games_played,
        "wins": wins,
        "losses": games_played - wins,
        "win_rate": round((wins / games_played) * 100, 1) if games_played else 0,
        "games_as_goat": games.filter(goat_player=user).count(),
        "wins_as_goat": games.filter(goat_player=user, winner_role="goat").count(),
        "games_as_tiger": games.filter(tiger_player=user).count(),
        "wins_as_tiger": games.filter(tiger_player=user, winner_role="tiger").count(),
    }