from flask import jsonify
from functools import wraps


def unique(a):
    return list(set(a))


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
