class Error(Exception): pass

def is_enabled(*args, **kargs):
    return variant(*args, **kargs) == 'on'

def variant(feature, instance=None, bucket_id=None):
    if instance is None and bucket_id is None:
        raise ValueError('Either an instance or a bucket_id must be specified.')
    if bucket_id is None:
        if instance is not None:
            bucket_id = instance.id

    return 'on'
