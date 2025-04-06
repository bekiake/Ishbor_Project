from django.contrib import admin
from .models import User, Worker, Feedback
from .forms import FeedbackForm


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
    form = FeedbackForm
    list_display = ('id', 'worker', 'user', 'rate', 'text', 'create_at')
    search_fields = ('worker__name', 'user__name', 'text')
    list_filter = ('rate',)
    ordering = ('-create_at',)
    
    # Fieldsets orqali formadagi maydonlarni ko'rsatish
    fieldsets = (
        (None, {
            'fields': ('worker', 'user', 'rate', 'text')  # Tanlash maydonlari
        }),
    )
