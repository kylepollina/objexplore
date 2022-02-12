def is_empty(obj):
    """ Check to see if the object is equal to any of the following objects """
    return not any(obj is x for x in [None, [], (), {}, set()])
    # try:
    #     return not any(obj is x for x in [None, [], (), {}, set()])
    # except Exception:
    #     # TODO this might not be needed anymore
    #     return True
