def is_selectable(obj):
    try:
        return obj not in (None, [], (), {}, set())
    except ValueError:
        return True
