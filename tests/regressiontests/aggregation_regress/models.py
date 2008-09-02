# coding: utf-8
from django.db import models

class Author(models.Model):
   name = models.CharField(max_length=100)
   age = models.IntegerField()
   friends = models.ManyToManyField('self', blank=True)

   def __unicode__(self):
      return self.name

   class Admin:
      pass

class Publisher(models.Model):
   name = models.CharField(max_length=300)
   num_awards = models.IntegerField()
   
   def __unicode__(self):
      return self.name

   class Admin:
      pass

class Book(models.Model):
   isbn = models.CharField(max_length=9)
   name = models.CharField(max_length=300)
   pages = models.IntegerField()
   price = models.FloatField()
   authors = models.ManyToManyField(Author)
   publisher = models.ForeignKey(Publisher)
   
   def __unicode__(self):
      return self.name

   class Admin:
      pass

class Store(models.Model):
   name = models.CharField(max_length=300)
   books = models.ManyToManyField(Book)
   
   def __unicode__(self):
      return self.name

   class Admin:
      pass

#Extra does not play well with values. Modify the tests if/when this is fixed.
__test__ = {'API_TESTS': """
>>> from django.core import management
>>> from django.db.models import get_app

# Reset the database representation of this app.
# This will return the database to a clean initial state.
>>> management.call_command('flush', verbosity=0, interactive=False)

>>> from django.db.aggregates import Avg, Sum, Count, Max, Min

>>> Book.objects.all().aggregate(Sum('pages'), Avg('pages'))
{'pages__sum': 3703.0, 'pages__avg': 617.1...}

>>> Book.objects.all().values().aggregate(Sum('pages'), Avg('pages'))
{'pages__sum': 3703.0, 'pages__avg': 617.1...}

>>> Book.objects.all().extra(select={'price_per_page' : 'price / pages'}).aggregate(Sum('pages'))
{'pages__sum': 3703.0}

>>> Book.objects.all().annotate(mean_auth_age=Avg('authors__age')).extra(select={'price_per_page' : 'price / pages'}).get(pk=1).__dict__
{'mean_auth_age': 34.5, 'isbn': u'159059725', 'name': u'The Definitive Guide to Django: Web Development Done Right', 'price_per_page': 0.067..., 'price': 30.0, 'id': 1, 'publisher_id': 1, 'pages': 447}

>>> Book.objects.all().extra(select={'price_per_page' : 'price / pages'}).annotate(mean_auth_age=Avg('authors__age')).get(pk=1).__dict__
{'mean_auth_age': 34.5, 'isbn': u'159059725', 'name': u'The Definitive Guide to Django: Web Development Done Right', 'price_per_page': 0.067..., 'price': 30.0, 'id': 1, 'publisher_id': 1, 'pages': 447}

>>> Book.objects.all().annotate(mean_auth_age=Avg('authors__age')).extra(select={'price_per_page' : 'price / pages'}).values().get(pk=1)
{'mean_auth_age': 34.5, 'isbn': u'159059725', 'name': u'The Definitive Guide to Django: Web Development Done Right', 'price_per_page': 0.067..., 'price': 30.0, 'id': 1, 'publisher_id': 1.0, 'pages': 447}

>>> Book.objects.all().annotate(mean_auth_age=Avg('authors__age')).extra(select={'price_per_page' : 'price / pages'}).values('name').get(pk=1)
{'mean_auth_age': 34.5, 'name': u'The Definitive Guide to Django: Web Development Done Right'}

>>> Book.objects.all().values().annotate(mean_auth_age=Avg('authors__age')).extra(select={'price_per_page' : 'price / pages'}).get(pk=1)
{'mean_auth_age': 34.5, 'isbn': u'159059725', 'name': u'The Definitive Guide to Django: Web Development Done Right', 'price_per_page': 0.067..., 'price': 30.0, 'id': 1, 'publisher_id': 1.0, 'pages': 447}

>>> Book.objects.all().values('name').annotate(mean_auth_age=Avg('authors__age')).extra(select={'price_per_page' : 'price / pages'}).get(pk=1)
{'mean_auth_age': 34.5, 'name': u'The Definitive Guide to Django: Web Development Done Right'}

#Check that all of the objects are getting counted (allow_nulls) and that values respects the amount of objects 
>>> len(Author.objects.all().annotate(Avg('friends__age')).values())
9

#Check that consecutive calls to annotate dont break group by
>>> Book.objects.values('price').annotate(oldest=Max('authors__age')).order_by('oldest').annotate(Max('publisher__num_awards'))
[{'price': 30.0, 'oldest': 35.0, 'publisher__num_awards__max': 3.0}, {'price': 29.69..., 'oldest': 37.0, 'publisher__num_awards__max': 7.0}, {'price': 23.09, 'oldest': 45.0, 'publisher__num_awards__max': 1.0}, {'price': 75.0, 'oldest': 57.0, 'publisher__num_awards__max': 9.0}, {'price': 82.7..., 'oldest': 57.0, 'publisher__num_awards__max': 7.0}]

#Checks fixed bug with multiple aggregate objects in the aggregate call
>>> Book.objects.all().annotate(num_authors=Count('authors__id')).aggregate(Max('price'), Sum('num_authors'))
{'num_authors__sum': 10.0, 'price__max': 82.7...}

"""
}
