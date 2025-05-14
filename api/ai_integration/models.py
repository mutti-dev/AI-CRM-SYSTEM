from django.db import models

class FineTunedDataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    data = models.JSONField()  # Store the fine-tuned dataset as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name




class TokenUsageLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    model_name = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    total_tokens = models.IntegerField()
    source = models.CharField(max_length=50, default="unknown")  # e.g., outlook, teams, etc.

    def __str__(self):
        return f"{self.timestamp} - {self.model_name}: {self.total_tokens} tokens"
