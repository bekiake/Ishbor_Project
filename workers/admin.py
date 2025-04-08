from django.contrib import admin

from app.models.models import Skills
from .models import User, Worker, Feedback

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_id', 'name', 'created', 'updated')
    search_fields = ('telegram_id', 'name')
    ordering = ('-created',)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_id', 'name', 'phone', 'gender', 'payment_type', 'daily_payment', 'created_at')
    list_filter = ('payment_type', 'gender')
    search_fields = ('telegram_id', 'name', 'phone', 'languages', 'skills')
    ordering = ('-created_at',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'worker', 'user', 'rate', 'create_at')
    list_filter = ('rate',)
    search_fields = ('worker__name', 'user__name', 'text')
    ordering = ('-create_at',)

@admin.register(Skills)