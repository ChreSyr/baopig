
def is_one_of_types(o, *types):
    return isinstance(o, types)
    return True in [isinstance(o, t) for t in types], "{} must be one of {} types, got {} instead".format(o, types, type(o))

def is_iterable(o, k):
    if not hasattr(o, "__iter__"): return False
    return len(o) == k

def is_typed_iterable(o, t, k):
    if not hasattr(o, "__iter__"): return False
    if not len(o) == k: return False
    for elt in o:
        if not isinstance(elt, t): return False
    return True

def is_point(o):
    if not hasattr(o, "__iter__"): return False
    if not len(o) == 2: return False
    for coord in o:
        if not is_one_of_types(coord, int, float): return False
    return True

def is_size(o):
    if not hasattr(o, "__iter__"): return False
    if not len(o) == 2: return False
    for coord in o:
        if not is_one_of_types(coord, int, float): return False
        if not coord >= 0: return False
    return True

def is_color(o):
    if not hasattr(o, "__iter__"): return False
    if not len(o) in (3, 4): return False
    for elt in o:
        if not isinstance(elt, int): return False
        if not 0 <= elt <= 255: return False
    return True
