from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar_url',
            'last_login_at',
            'date_joined'
        ]
        read_only_fields = [
            'id',
            'email',
            'last_login_at',
            'date_joined'
        ]

    def validate_username(self, value):
        """
        Ensure username is unique and valid
        """
        if User.objects.exclude(id=self.instance.id if self.instance else None)\
                      .filter(username=value)\
                      .exists():
            raise serializers.ValidationError("This username is already taken.")
        return value