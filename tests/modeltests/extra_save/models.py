"""test for bug #8990
"""

from django.db import models

class Shelf(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return u"%s the shelf" % self.name


class BookManager(models.Manager):
    def get_query_set(self):
        return super(BookManager, self).get_query_set().\
            select_related('shelf').\
            extra(select={'shelf_name': 'extra_save_shelf.name'})


class Book(models.Model):
    name = models.CharField(max_length=50)
    shelf = models.ForeignKey(Shelf)

    objects = BookManager()

    def __unicode__(self):
        return u"%s the book" % self.name


__test__ = {'API_TESTS':"""
>>> shelf = Shelf(name="Foo")
>>> shelf.save()
>>> book = Book(name="bar", shelf=shelf)
>>> book.save()              # initial save works fine

>>> Book.objects.get(pk=1)   # querying works as well
<Book: bar the book>

# subsequent saves work too...
>>> book.save()

# ...instead of failing with:
#Traceback (most recent call last):
#    ...
#OperationalError: no such column: extra_save_shelf.name
"""
}