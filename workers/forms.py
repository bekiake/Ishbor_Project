from django import forms
from .models import Feedback, Worker, User

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['worker', 'user', 'rate', 'text']
    
    # Sizning talablaringizga mos ravishda to'ldirish maydonlarini qo'shishingiz mumkin
    # Misol uchun:
    def clean_worker(self):
        worker = self.cleaned_data.get('worker')
        if not worker:
            raise forms.ValidationError("Worker is required")
        return worker

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not user:
            raise forms.ValidationError("User is required")
        return user
