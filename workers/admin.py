from django.contrib import admin

from .models import User, Worker, Feedback, Skills
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


admin.site.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    form = FeedbackForm
    list_display = ('id', 'worker_name', 'user', 'rate', 'text', 'create_at')  # worker_name ni qo‘shish
    search_fields = ('worker__name', 'user__name', 'text')
    list_filter = ('rate',)
    ordering = ('-create_at',)

    fieldsets = (
        (None, {
            'fields': ('worker', 'user', 'rate', 'text')
        }),
    )

    def worker_name(self, obj):
        return obj.worker.name if obj.worker else None  # worker.name ni ko‘rsatish
    worker_name.admin_order_field = 'worker__name'  # Sort qilish uchun
    worker_name.short_description = 'Worker Name'  # Sarlavha


@admin.register(Skills)
class SkillsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # 'name' yoki o'zingiz istagan maydonlar
    search_fields = ('name',)  # 'name' ustida qidiruv
    ordering = ('name',)
