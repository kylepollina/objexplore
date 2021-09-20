def is_selectable(obj):
    try:
        bool(obj)
    except ValueError:
        return True
    else:
        return obj not in (None, [], (), {}, set())
