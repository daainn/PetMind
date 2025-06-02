from django.db import models
from user.models import User

class DogBreed(models.Model):
    name = models.CharField(max_length=100)  
    image_url = models.URLField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class DogProfile(models.Model):
    GENDER_CHOICES = [('남아', '남아'), ('여아', '여아')]
    NEUTER_CHOICES = [('완료', '완료'), ('미완료', '미완료'), ('모름', '모름')]
    LIVING_PERIOD_CHOICES = [
    ('1년 미만', '1년 미만'),
    ('3년 미만', '3년 미만'),
    ('10년 미만', '10년 미만'),
    ('10년 이상', '10년 이상'),
    ]
    HOUSING_CHOICES = [
        ('아파트', '아파트'),
        ('단독주택', '단독주택'),
        ('빌라/다세대', '빌라/다세대'),
        ('기타', '기타')
    ]

    user = models.ForeignKey(User,on_delete=models.CASCADE,to_field='id')
    breed = models.ForeignKey(DogBreed, on_delete=models.CASCADE)  # 필수
    name = models.CharField(max_length=100)                        # 필수
    breed_name = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    neutered = models.CharField(max_length=10, choices=NEUTER_CHOICES, null=True, blank=True)
    disease_history = models.TextField(null=True, blank=True)
    living_period = models.CharField(max_length=30, choices=LIVING_PERIOD_CHOICES, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    housing_type = models.CharField(max_length=20, choices=HOUSING_CHOICES, null=True, blank=True)
    profile_image_url = models.URLField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
