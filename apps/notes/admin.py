from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Note


@admin.register(Note)
class NoteAdmin(SimpleHistoryAdmin):
    list_display = ["title", "owner", "is_archived", "created_at"]
    list_filter = ["is_archived"]
    search_fields = ["title", "owner__username"]
    autocomplete_fields = ["owner"]
