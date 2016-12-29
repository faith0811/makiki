# -*- coding: utf-8 -*-

import collections


Type = collections.namedtuple('Type', ['name', '_type', 'examples'])


class SchemaMeta(type):
    def __init__(self, name, parents, attrs):
        super().__init__(name, parents, attrs)
        assert isinstance(attrs['fields'])
        for field in attrs['fields']:
            assert isinstance(field, Type)


class BasicSchema(object, metaclass=SchemaMeta):
    fields = []
