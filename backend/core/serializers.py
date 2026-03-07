from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    win_rate = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "games_played",
            "wins",
            "losses",
            "win_rate",
            "avatar_url",
            "is_guest"
        ]

    def get_win_rate(self, obj):
        return obj.win_rate()

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            return (
                request.build_absolute_uri(obj.avatar.url)
                if request
                else obj.avatar.url
            )
        return None
