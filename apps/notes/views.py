from rest_framework.viewsets import ModelViewSet

from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(ModelViewSet):
    serializer_class = NoteSerializer
    filterset_fields = ["is_archived"]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "updated_at", "title"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Note.objects.none()
        return Note.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
