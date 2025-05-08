from django.db import models

class FAQ(models.Model):
    question = models.TextField(unique=True)
    answer = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords for NLP/Keyword matching.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
