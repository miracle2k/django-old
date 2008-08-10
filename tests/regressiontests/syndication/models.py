from django.db import models
import datetime

class Article(models.Model):
    title = models.CharField(max_length=250)
    text = models.TextField()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return "/%s/" % self.id
