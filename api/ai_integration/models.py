from django.db import models

class FineTunedDataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    data = models.JSONField()  # Store the fine-tuned dataset as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
