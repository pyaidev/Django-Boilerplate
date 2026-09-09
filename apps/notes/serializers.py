from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "owner", "title", "body", "is_archived", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
