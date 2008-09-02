# coding: utf-8
from django.db import models

class Author(models.Model):
   name = models.CharField(max_length=100)
   age = models.IntegerField()
   friends = models.ManyToManyField('self', blank=True)

   def __unicode__(self):
      return self.name

class Publisher(models.Model):
   name = models.CharField(max_length=300)
   num_awards = models.IntegerField()
   
   def __unicode__(self):
      return self.name

class Book(models.Model):
   isbn = models.CharField(max_length=9)
   name = models.CharField(max_length=300)
   pages = models.IntegerField()
   price = models.FloatField()
   authors = models.ManyToManyField(Author)
   publisher = models.ForeignKey(Publisher)
   
   def __unicode__(self):
      return self.name

class Store(models.Model):
   name = models.CharField(max_length=300)
   books = models.ManyToManyField(Book)
   
   def __unicode__(self):
      return self.name

class Entries(models.Model):
   EntryID = models.AutoField(primary_key=True, db_column='Entry ID')
   Entry = models.CharField(unique=True, max_length=50)
   Exclude = models.BooleanField()

class Clues(models.Model):
   ID = models.AutoField(primary_key=True)
   EntryID = models.ForeignKey(Entries, verbose_name='Entry', db_column = 'Entry ID')
   Clue = models.CharField(max_length=150, core=True)

# Tests on 'aggergate'
# Different backends and numbers.
__test__ = {'API_TESTS': """
>>> from django.core import management

# Reset the database representation of this app.
# This will return the database to a clean initial state.
>>> management.call_command('flush', verbosity=0, interactive=False)

# Empty Call 
>>> Author.objects.all().aggregate()
{}

>>> from django.db.aggregates import Avg, Sum, Count, Max, Min

# Note that rounding of floating points is being used for the tests to
# pass for all backends

# Single model aggregation
#

# Simple
# Average Author age
>>> Author.objects.all().aggregate(Avg('age'))
{'age__avg': 37.4...}

# Multiple
# Average and Sum of Author's age
>>> Author.objects.all().aggregate(Sum('age'), Avg('age'))
{'age__sum': 337.0, 'age__avg': 37.4...}

# After aplying other modifiers
# Sum of the age of those older than 29 years old
>>> Author.objects.all().filter(age__gt=29).aggregate(Sum('age'))
{'age__sum': 254.0}

# Depth-1 Joins
#

# On Relationships with self 
# Average age of those with friends (not exactelly.
# That would be: Author.objects.all().exclude(friends=None).aggregate(Avg('age')))
>>> Author.objects.all().aggregate(Avg('friends__age'))
{'friends__age__avg': 34.07...}

# On ManyToMany Relationships
#

# Forward
# Average age of the Authors of Books that cost less than 50 USD
>>> Book.objects.all().filter(price__lt=50).aggregate(Avg('authors__age'))
{'authors__age__avg': 33.42...}


# Backward
# Average price of the Books whose Author's name contains the letter 'a' 
>>> Author.objects.all().filter(name__contains='a').aggregate(Avg('book__price'))
{'book__price__avg': 37.54...}

# On OneToMany Relationships
#

# Forward
# Sum of the number of awards of each Book's Publisher
>>> Book.objects.all().aggregate(Sum('publisher__num_awards'))
{'publisher__num_awards__sum': 30.0}

# Backward
# Sum of the price of every Book that has a Publisher
>>> Publisher.objects.all().aggregate(Sum('book__price'))
{'book__price__sum': 270.269...}

# Multiple Joins
#

#Forward
>>> Store.objects.all().aggregate(Max('books__authors__age'))
{'books__authors__age__max': 57.0}

#Backward
>>> Author.objects.all().aggregate(Min('book__publisher__num_awards'))
{'book__publisher__num_awards__min': 1.0}

# You can also use aliases.
# 

# Average amazon.com Book price
>>> Store.objects.filter(name='Amazon.com').aggregate(amazon_mean=Avg('books__price'))
{'amazon_mean': 45.04...}

# Tests on annotate()
#

# An empty annotate call does nothing but return the same QuerySet
>>> Book.objects.all().annotate().order_by('pk')
[<Book: The Definitive Guide to Django: Web Development Done Right>, <Book: Sams Teach Yourself Django in 24 Hours>, <Book: Practical Django Projects>, <Book: Python Web Development with Django>, <Book: Artificial Intelligence: A Modern Approach>, <Book: Paradigms of Artificial Intelligence Programming: Case Studies in Common Lisp>]

#Annotate inserts the alias into the model object with the aggregated result
>>> books = Book.objects.all().annotate(mean_age=Avg('authors__age'))
>>> books.get(pk=1).name
u'The Definitive Guide to Django: Web Development Done Right'

>>> books.get(pk=1).mean_age
34.5

#Calls to values() are not commutative over annotate().

#Calling values on a queryset that has annotations returns the output
#as a dictionary
>>> Book.objects.filter(pk=1).annotate(mean_age=Avg('authors__age')).values()
[{'isbn': u'159059725', 'name': u'The Definitive Guide to Django: Web Development Done Right', 'price': 30.0, 'id': 1, 'publisher_id': 1, 'pages': 447, 'mean_age': 34.5}]

#Calling it with paramters reduces the output but does not remove the
#annotation.
>>> Book.objects.filter(pk=1).annotate(mean_age=Avg('authors__age')).values('name')
[{'name': u'The Definitive Guide to Django: Web Development Done Right', 'mean_age': 34.5}]

#An empty values() call before annotating has the same effect as an
#empty values() call after annotating
>>> Book.objects.filter(pk=1).values().annotate(mean_age=Avg('authors__age'))
[{'isbn': u'159059725', 'name': u'The Definitive Guide to Django: Web Development Done Right', 'price': 30.0, 'id': 1, 'publisher_id': 1, 'pages': 447, 'mean_age': 34.5}]

#Calling annotate() on a ValuesQuerySet annotates over the groups of
#fields to be selected by the ValuesQuerySet.

#Note that an extra parameter is added to each dictionary. This
#parameter is a queryset representing the objects that have been
#grouped to generate the annotation

>>> Book.objects.all().values('price').annotate(number=Count('authors__id'), mean_age=Avg('authors__age')).order_by('price')
[{'price': 23.09, 'number': 1.0, 'mean_age': 45.0}, {'price': 29.690000000000001, 'number': 4.0, 'mean_age': 30.0}, {'price': 30.0, 'number': 2.0, 'mean_age': 34.5}, {'price': 75.0, 'number': 1.0, 'mean_age': 57.0}, {'price': 82.799999999999997, 'number': 2.0, 'mean_age': 51.5}]


#Notice that the output includes all Authors but the value of the aggregation
#is 0 for those that have no friends.
#(consider having a neutral ('zero') element for each operation) 
>>> authors = Author.objects.all().annotate(Avg('friends__age')).order_by('id')
>>> len(authors)
9
>>> for i in authors:
...     print i.name, i.friends__age__avg
...
Adrian Holovaty 32.0
Jacob Kaplan-Moss 29.5
Brad Dayley None
James Bennett 34.0
Jeffrey Forcier  27.0
Paul Bissex 31.0
Wesley J. Chun 33.66...
Peter Norvig 46.0
Stuart Russell 57.0

#The Count aggregation function allows an extra parameter: distinct.
#
>>> Book.objects.all().aggregate(Count('price'))
{'price__count': 6.0}

>>> Book.objects.all().aggregate(Count('price', distinct=True))
{'price__count': 5.0}

#Retreiving the grouped objects


#When using Count you can also ommit the primary key and refer only to
#the related field name if you want to count all the related objects
#and not a specific column
>>> explicit = list(Author.objects.annotate(Count('book__id')))
>>> implicit = list(Author.objects.annotate(Count('book')))
>>> explicit == implicit
True

##
# Ordering is allowed on aggregates
>>> Book.objects.values('price').annotate(oldest=Max('authors__age')).order_by('oldest')
[{'price': 30.0, 'oldest': 35.0}, {'price': 29.6..., 'oldest': 37.0}, {'price': 23.09, 'oldest': 45.0}, {'price': 75.0, 'oldest': 57.0}, {'price': 82.7..., 'oldest': 57.0}]

>>> Book.objects.values('price').annotate(oldest=Max('authors__age')).order_by('-oldest')
[{'price': 75.0, 'oldest': 57.0}, {'price': 82.7..., 'oldest': 57.0}, {'price': 23.09, 'oldest': 45.0}, {'price': 29.6..., 'oldest': 37.0}, {'price': 30.0, 'oldest': 35.0}]

>>> Book.objects.values('price').annotate(oldest=Max('authors__age')).order_by('-oldest', 'price')
[{'price': 75.0, 'oldest': 57.0}, {'price': 82.7..., 'oldest': 57.0}, {'price': 23.09, 'oldest': 45.0}, {'price': 29.6..., 'oldest': 37.0}, {'price': 30.0, 'oldest': 35.0}]

>>> Book.objects.values('price').annotate(oldest=Max('authors__age')).order_by('-oldest', '-price')
[{'price': 82.7..., 'oldest': 57.0}, {'price': 75.0, 'oldest': 57.0}, {'price': 23.09, 'oldest': 45.0}, {'price': 29.6..., 'oldest': 37.0}, {'price': 30.0, 'oldest': 35.0}]

# It is possible to aggregate over anotated values
# 
>>> Book.objects.all().annotate(num_authors=Count('authors__id')).aggregate(Avg('num_authors'))
{'num_authors__avg': 1.66...}

# You can filter the results based on the aggregation alias.
# 

#Lets add a publisher to test the different possibilities for filtering
>>> p = Publisher(name='Expensive Publisher', num_awards=0)
>>> p.save()
>>> Book(name='ExpensiveBook1', pages=1, isbn='111', price=1000, publisher=p).save()
>>> Book(name='ExpensiveBook2', pages=1, isbn='222', price=1000, publisher=p).save()
>>> Book(name='ExpensiveBook3', pages=1, isbn='333', price=35, publisher=p).save()

#Consider the following queries:

#Publishers that have:

#(i) more than one book
>>> Publisher.objects.annotate(num_books=Count('book__id')).filter(num_books__gt=1).order_by('pk')
[<Publisher: Apress >, <Publisher: Prentice Hall>, <Publisher: Expensive Publisher>]

#(ii) a book that cost less than 40
>>> Publisher.objects.filter(book__price__lt=40).order_by('pk')
[<Publisher: Apress >, <Publisher: Apress >, <Publisher: Sams>, <Publisher: Prentice Hall>, <Publisher: Expensive Publisher>]

#(iii) more than one book and (at least) a book that cost less than 40
>>> Publisher.objects.annotate(num_books=Count('book__id')).filter(num_books__gt=1, book__price__lt=40).order_by('pk')
[<Publisher: Apress >, <Publisher: Prentice Hall>, <Publisher: Expensive Publisher>]

#(iv) more than one book that costs less than 40
>>> Publisher.objects.filter(book__price__lt=40).annotate(num_books=Count('book__id')).filter(num_books__gt=1).order_by('pk')
[<Publisher: Apress >]

# Now a bit of testing on the different lookup types
# 

>>> Publisher.objects.annotate(num_books=Count('book')).filter(num_books__range=[1, 3]).order_by('pk')
[<Publisher: Apress >, <Publisher: Sams>, <Publisher: Prentice Hall>, <Publisher: Morgan Kaufmann>, <Publisher: Expensive Publisher>]

>>> Publisher.objects.annotate(num_books=Count('book')).filter(num_books__range=[1, 2]).order_by('pk')
[<Publisher: Apress >, <Publisher: Sams>, <Publisher: Prentice Hall>, <Publisher: Morgan Kaufmann>]

>>> Publisher.objects.annotate(num_books=Count('book')).filter(num_books__in=[1, 3]).order_by('pk')
[<Publisher: Sams>, <Publisher: Morgan Kaufmann>, <Publisher: Expensive Publisher>]

>>> Publisher.objects.annotate(num_books=Count('book')).filter(num_books__isnull=True)
[]

>>> p.delete()

# Community tests
#

#Thanks to Russell for the following set
#

#Does Author X have any friends? (or better, how many friends does author X have)
>> Author.objects.filter(pk=1).aggregate(Count('friends__id'))
{'friends__id__count': 2.0}

#Give me a list of all Books with more than 1 authors
>>> Book.objects.all().annotate(num_authors=Count('authors__name')).filter(num_authors__ge=2).order_by('pk')
[<Book: The Definitive Guide to Django: Web Development Done Right>, <Book: Artificial Intelligence: A Modern Approach>]

#Give me a list of all Authors that have no friends
>>> Author.objects.all().annotate(num_friends=Count('friends__id', distinct=True)).filter(num_friends=0).order_by('pk')
[<Author: Brad Dayley>]

#Give me a list of all publishers that have published more than 1 books
>>> Publisher.objects.all().annotate(num_books=Count('book__id')).filter(num_books__gt=1).order_by('pk')
[<Publisher: Apress >, <Publisher: Prentice Hall>]

#Give me a list of all publishers that have published more than 1 books that cost less than 30
#>>> Publisher.objects.all().filter(book__price__lt=40).annotate(num_books=Count('book__id')).filter(num_books__gt=1)
[<Publisher: Apress >]

#Give me a list of all Books that were written by X and one other author. 
>>> Book.objects.all().annotate(num_authors=Count('authors__id')).filter(authors__name__contains='Norvig', num_authors__gt=1)
[<Book: Artificial Intelligence: A Modern Approach>]

#Give me the average price of all Books that were written by X and one other author.
#(Aggregate over objects discovered using membership of the m2m set)

#Adding an existing author to another book to test it the right way
>>> a = Author.objects.get(name__contains='Norvig')
>>> b = Book.objects.get(name__contains='Done Right')
>>> b.authors.add(a)
>>> b.save()

#This should do it
>>> Book.objects.all().annotate(num_authors=Count('authors__id')).filter(authors__name__contains='Norvig', num_authors__gt=1).aggregate(Avg('price'))
{'price__avg': 56.39...}
>>> b.authors.remove(a)

#
# --- Just one of the hard ones left ---
#

#Give me a list of all Authors that have published a book with at least one other person
#(Filters over a count generated on a related object)
#
# Cheating: [a for a in Author.objects.all().annotate(num_coleagues=Count('book__authors__id'), num_books=Count('book__id', distinct=True)) if a.num_coleagues - a.num_books > 0]
# F-Syntax is required. Will be fixed after F objects are available


#Thanks to Karen for the following set
# Tests on fields with different names and spaces. (but they work =) )

>>> Clues.objects.values('EntryID__Entry').annotate(Appearances=Count('EntryID'), Distinct_Clues=Count('Clue', distinct=True))
[]

"""}
