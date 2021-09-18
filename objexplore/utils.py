

def is_selectable(obj):
    return obj not in (None, [], (), {}, set()) and not callable(obj)
