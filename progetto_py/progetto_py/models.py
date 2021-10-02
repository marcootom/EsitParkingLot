from django.db import models


class Park(models.Model):
    name = models.CharField(max_length=50, primary_key=True)

