from django.db import models

class CityData(models.Model):
    img = models.ImageField(upload_to='img')
    sound = models.FileField(upload_to='sound')
    prompt = models.CharField(max_length=50)

class UserInput(models.Model):

    prompt = models.CharField(max_length=50)
    # 1 街に住んでる人 2 そうではない人
    is_citizen = models.BooleanField(default=False)
    # 0 稽古場 1 電気湯 2 float 3 UR
    place_category = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)