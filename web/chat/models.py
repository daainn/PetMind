from django.db import models
from dogs.models import DogProfile
from user.models import User


class Chat(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # ✅ 추가
    dog = models.ForeignKey(DogProfile, null=True, blank=True, on_delete=models.SET_NULL)
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
    

class MessageImage(models.Model):
    message = models.ForeignKey(Message, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="chat_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Content(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reference_url = models.URLField(max_length=1000, null=True, blank=True)

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
