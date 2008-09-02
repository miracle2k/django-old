"""
Classes to represent the default aggregate functions
"""

from django.db.models.sql.constants import LOOKUP_SEP
from django.core.exceptions import FieldError

def interpolate(templateStr, **kws):
    from string import Template
    return Template(templateStr).substitute(kws)

class Aggregate(object):
    """
    Default Aggregate.
    func
    """
    def __init__(self, lookup):
        self.func = self.__class__.__name__.upper()
        self.lookup = lookup
        self.field_name = self.lookup.split(LOOKUP_SEP)[-1]
        self.aliased_name = '%s__%s' % (self.lookup,
                                        self.__class__.__name__.lower())
        self.sql_template = '${func}(${field})'

    def relabel_aliases(self, change_map):
        if self.col_alias in change_map:
            self.col_alias = change_map[self.col_alias]

    def as_fold(self, quote_func=None):
        """
        Pleas make me a better function! :(
        """
        #CK
        if self.lookup != self.field_name:
            raise FieldError('Joins are not allowed here.')
        #check to raise other exceptions
        return '%s(%s)' % (self.func, self.lookup)

    def as_sql(self, quote_func=None):
        if not quote_func:
            quote_func = lambda x: x
        return interpolate(self.sql_template,
                           func=self.func.upper(),
                           field='.'.join([quote_func(self.col_alias),
                                           quote_func(self.column)]))
                           
class Max(Aggregate):
    pass

class Min(Aggregate):
    pass

class Avg(Aggregate):
    pass

class Sum(Aggregate):
    pass

class Count(Aggregate):
    def __init__(self, lookup, distinct=False):
        if distinct:
            distinct = 'DISTINCT '
        else:
            distinct = ''
        super(Count, self).__init__(lookup)
        self.sql_template = '${func}(%s${field})' % distinct
        
        

