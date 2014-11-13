from flask import jsonify
from functools import wraps


def unique(seq):
    """ Perserves the order of the elements in the original sequense """

    seen = set()
    for i in seq:
        if i not in seen:
            seen.add(i)
            yield i


def handle_exception_as_json(exc=Exception):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
                return jsonify({"result": True})
            except Exception, e:
                return jsonify({"result": False, "reason": unicode(e)})
        return wrapper
    return decorator
