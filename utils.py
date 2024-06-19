import datetime

def object_to_json_handler(object: any) -> any:
    if isinstance(object, datetime.datetime):
        return object.isoformat()
    else:
        return object.__dict__