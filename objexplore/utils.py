def is_selectable(obj):
    try:
        return obj not in (None, [], (), {}, set())
    except Exception:
        return True
