from flask.json import JSONEncoder
from datetime import datetime, date

class JQJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
                return datetime.strftime(obj, TIME_FORMAT)
            # if type date
            elif isinstance(obj, date):
                TIME_FORMAT = '%Y-%m-%d'
                return datetime.strftime(obj, TIME_FORMAT)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)