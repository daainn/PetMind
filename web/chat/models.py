from django.db import models
from dogs.models import DogProfile
from user.models import User


class Chat(models.Model):
    dog = models.ForeignKey(DogProfile, on_delete=models.CASCADE)
    chat_title = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.chat_title or f"Chat {self.id}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=[('user', 'user'), ('bot', 'bot')])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:20]}"


class Content(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    image_url = models.URLField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reference_url = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.title


class ContentRecommendation(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('content', 'chat')


class UserReview(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    review_score = models.IntegerField()
    review = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"리뷰 {self.review_score}점 - {self.chat_id}"
