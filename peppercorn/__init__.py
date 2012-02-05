import functools
from peppercorn.compat import next

def data_type(value):
    if ':' in value:
        return [ x.strip() for x in value.rsplit(':', 1) ]
    return ('', value.strip())

START = '__start__'
END = '__end__'
SEQUENCE = 'sequence'
MAPPING = 'mapping'
RENAME = 'rename'


class ParseError(Exception):
    """
    An exception raised by :func:`parse` when the input is malformed.
    """


def stream(next_token_gen, token):
    """
    thanks to the effbot for
    http://effbot.org/zone/simple-iterator-parser.htm
    """
    op, data = token
    if op == START:
        name, typ = data_type(data)
        out = []
        if typ in (SEQUENCE, MAPPING, RENAME):
            if typ in (SEQUENCE, RENAME):
                out = []
                add = lambda x, y: out.append(y)
            else:
                out = {}
                add = out.__setitem__
            token = next_token_gen()
            op, data = token
            while op != END:
                key, val = stream(next_token_gen, token)
                add(key, val)
                token = next_token_gen()
                op, data = token
            if typ == RENAME:
                if out:
                    out = out[0]
                else:
                    out = ''
            return name, out
        else:
            raise ParseError('Unknown stream start marker %s' % repr(token))
    else:
        return op, data

def parse(fields):
    """ Infer a data structure from the ordered set of fields and
    return it.

    A :exc:`ParseError` is raised if a data structure can't be inferred.
    """
    fields = [(START, MAPPING)] + list(fields) + [(END,'')]
    src = iter(fields)
    try:
        result = stream(functools.partial(next, src), next(src))[1]
    except StopIteration:
        raise ParseError('Unclosed sequence')
    except RuntimeError:
        raise ParseError('Input too deeply nested')
    return result
