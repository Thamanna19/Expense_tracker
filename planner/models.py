from django.db import models
from django.contrib.auth.models import User


class DailyBudget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000)

    def __str__(self):
        return f"{self.user.username}'s budget"


class Expense(models.Model):
    class Category(models.TextChoices):
        FOOD = 'food', 'Food'
        TRAVEL = 'travel', 'Travel'
        EDUCATION = 'education', 'Education'
        ENTERTAINMENT = 'entertainment', 'Entertainment'
        SHOPPING = 'shopping', 'Shopping'
        BILLS = 'bills', 'Bills'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=Category.choices)
    spent_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-spent_on', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount}"


class DailyNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_notes')
    note_date = models.DateField()
    content = models.TextField(blank=True, max_length=1000)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-note_date', '-updated_at']

    def __str__(self):
        return f"Note for {self.note_date}"

# Create your models here.

