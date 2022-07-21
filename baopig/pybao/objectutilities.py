import functools
import inspect
from collections import deque
from weakref import ref as wkref, WeakSet


def ref(obj, callback=None):
    if hasattr(obj, "get_weakref"):
        return obj.get_weakref(callback)
    return wkref(obj, callback)


class PrefilledFunction:
    def __init__(self, function, *args, **kwargs):
        assert callable(function), "function must be callable"

        self._function = function
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self._function(*self._args, *args, **self._kwargs, **kwargs)


class PackedFunctions:
    """
    This object allow tou to execute multiple function from one call

    WARNING : if you enter parameters, it will be distributed to all of the packed functions
    This means you cannot pack two functions if they each require differents parameters
    You cannot remove a function from a PackedFunctions
    """

    def __init__(self, *functions):

        self._functions = list()
        for func in functions:
            self.add(func)

    def __call__(self, *args, **kwargs):

        for func in self._functions:
            func(*args, **kwargs)

    def __str__(self):

        return "PackedFunctions{}".format(tuple(self._functions))

    def add(self, func, owner=None):
        """
        Owner parameter is usefull for remove
        It allow you to remove an element who own a method in a PackedFunctions
        because if you don't, the owner will not be deleted
        """

        assert callable(func)
        if owner is not None:
            setattr(func, "_owner", owner)
            owner.listof_packedfunctions.add(self)
        self._functions.append(func)

    def clear(self):

        self._functions.clear()

    def remove(self, func):

        self._functions.remove(func)

    def remove_funcs_of(self, owner):

        # funcs_to_remove = []
        for func in tuple(self._functions):
            if hasattr(func, "_owner"):
                if func._owner == owner:
                    # funcs_to_remove.append(func)
                    self._functions.remove(func)
        # for func in funcs_to_remove:


class Object:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def __str__(self) -> str:
        return "<{}({})>".format(self.__class__.__name__, str(self.__dict__)[1:-1])


class TypedDeque(deque):
    """
    A TypedDeque is a deque who can only contain items of type ItemsClass
    deque : a list-like sequence optimized for data accesses near its endpoints
    """

    def __init__(self, ItemsClass, seq=(), maxlen=None):
        """
        :param ItemsClass: the type for all deque items
        :param seq: an items sequence
        :param maxlen: the max deque length
        """

        assert inspect.isclass(ItemsClass), "ItemsClass must be a class"
        assert hasattr(seq, "__iter__"), "seq must be an iterable"
        assert maxlen is None or isinstance(maxlen, int), "maxlen must be an integer"

        self.ItemsClass = ItemsClass
        self.msg_item_type_error = "Only {} objects are accepted in this list".format(self.ItemsClass.__name__)

        for item in seq:
            self._check(item)
        deque.__init__(self, seq, maxlen)

    def __setitem__(self, index, p_object):
        self._check(p_object)

        deque.__setitem__(self, index, p_object)

    def __repr__(self):
        return "<TypedDeque({}):{}>".format(self.ItemsClass.__name__,
                                            "[{}]".format(", ".join(list((item.__str__() for item in self)))))

    def __str__(self):
        return "[{}]".format(", ".join(list((item.__str__() for item in self)))) + (
            ", maxlen={}".format(self.maxlen) if self.maxlen else "")

    def _check(self, p_object):
        if not self.accept(p_object):
            raise PermissionError(self.msg_item_type_error)

    def accept(self, p_object):
        return isinstance(p_object, self.ItemsClass)

    def append(self, p_object):
        self._check(p_object)

        deque.append(self, p_object)

    def appendleft(self, p_object):
        self._check(p_object)

        deque.appendleft(self, p_object)

    def extend(self, iterable):
        for p_object in iterable:
            self.append(p_object)

    def extendleft(self, iterable):
        for p_object in iterable:
            self.appendleft(p_object)

    def insert(self, index, p_object):
        self._check(p_object)

        deque.insert(self, index, p_object)


class TypedList(list):

    def __init__(self, *ItemsClass, seq=()):
        """
        Create a list who can only contain items of type ItemsClass
        :param ItemsClass: the type for all list items
        :type ItemsClass: class
        :param seq: an items sequence
        """
        list.__init__(self, seq)
        self.set_ItemsClass(*ItemsClass)

    def __setitem__(self, index, p_object):
        self._check(p_object)

        list.__setitem__(self, index, p_object)

    def __repr__(self):
        return "<{}(ItemsClass:{}, {}>".format(self.__class__.__name__, self.ItemsClass_name,
                                               "[{}]".format(", ".join(list((item.__str__() for item in self)))))

    def __str__(self):
        return "[{}]".format(", ".join(list((item.__str__() for item in self))))

    def _check(self, item):
        if not self.accept(item):
            raise PermissionError(self.msg_item_type_error.format(item.__class__.__name__))

    def accept(self, item):
        if inspect.isclass(item):
            return issubclass(item, self.ItemsClass)
        return isinstance(item, self.ItemsClass)

    def append(self, p_object):
        self._check(p_object)

        list.append(self, p_object)

    def extend(self, iterable):
        for p_object in iterable:
            self.append(p_object)

    def insert(self, index, p_object):
        self._check(p_object)

        list.insert(self, index, p_object)

    def set_ItemsClass(self, *ItemsClass):

        # try:
        for Class in ItemsClass:
            assert inspect.isclass(Class), "ItemsClass must be a class or a list of class"
        name = "(%s)" % ", ".join(Class.__name__ for Class in ItemsClass)
        # except TypeError:
        #     assert inspect.isclass(ItemsClass), "ItemsClass must be a class or a list of class"
        #     name = ItemsClass.__name__
        self.ItemsClass = ItemsClass
        self.ItemsClass_name = name
        self.msg_item_type_error = "Only {} objects are accepted in this list".format(self.ItemsClass_name) + \
                                   " (wrong object class:{})"
        for item in self:
            self._check(item)


class TypedSet(set):
    """
    A TypedSet is a unordered collection of unique elements
    who can only contain items of type ItemsClass

    seq is the optionnal initial sequence
    """

    def __init__(self, ItemsClass, seq=()):

        assert inspect.isclass(ItemsClass), "ItemsClass must be a class"
        assert hasattr(seq, "__iter__"), "seq must be an iterable"
        self.ItemsClass = ItemsClass
        self.msg_item_type_error = "Only {} objects are accepted in this list".format(self.ItemsClass.__name__)
        for item in seq:
            self._check(item)
        set.__init__(self, seq)

    def __repr__(self):
        return super().__repr__()
        # return "<TypedSet({}):{}>".format(self.ItemsClass.__name__, set.__str__(self))

    def __str__(self):
        return super().__str__()
        # return "{{}}".format(", ".join(list((item.__str__() for item in self))))

    def _check(self, item):
        if not self.accept(item):
            raise PermissionError(self.msg_item_type_error)

    def accept(self, item):
        return isinstance(item, self.ItemsClass)

    def add(self, item):
        """
        Add an item to a set.
        This has no effect if the item is already present.

        :param item: an item of type self.ItemsClass
        :return: None
        """
        self._check(item)

        set.add(self, item)

    def update(self, *args):
        """
        Add all items from args into a set
        if the items already is in the set, it isn't added

        S.update({1, 2, 3})
        S.update({1}, {2}, {3})

        :param args: a sequence of items sequence
        :return: None
        """
        for seq in args:
            for item in seq:
                self.add(item)


class History(deque):
    """
    An History is a TypedDeque whith a fixed size
    You can only :
        - append a new element in the history
        - read the history
    When you append a new element to the history, if it is full,
    the oldest element is removed
    The oldest element is positionned to the left

    Exemple :

            print(history) -> [2, 3, 4, 5, 6, 7, 8, 9]
                               ^                    ^
                        oldest element       newest element
    """

    def __init__(self, maxlen, seq=()):
        deque.__init__(self, seq, maxlen)

    def __delitem__(self, *args, **kwargs):
        raise PermissionError("Cannot use __delitem__ on an History")

    def __iadd__(self, *args, **kwargs):
        raise PermissionError("Cannot use __iadd__ on an History")

    def __imul__(self, *args, **kwargs):
        raise PermissionError("Cannot use __imul__ on an History")

    def __setitem__(self, index, p_object):
        raise PermissionError("Cannot use __setitem__ on an History")

    def appendleft(self, p_object):
        raise PermissionError("Cannot use appendleft on an History")

    def extendleft(self, iterable):
        raise PermissionError("Cannot use extendleft on an History")

    def insert(self, index, p_object):
        raise PermissionError("Cannot use insert on an History")

    def pop(self, *args, **kwargs):
        raise PermissionError("Cannot use pop on an History")

    def popleft(self, *args, **kwargs):
        raise PermissionError("Cannot use popleft on an History")

    def reverse(self):
        raise PermissionError("Cannot use reverse on an History")

    def rotate(self, *args, **kwargs):
        raise PermissionError("Cannot use rotate on an History")


class WeakList(list):
    """
    Create a TypedList who only store weak references to objects
    code from : https://stackoverflow.com/questions/677978/weakref-list-in-python
    """

    def __init__(self, seq=()):
        list.__init__(self)
        self._refs = []
        self._dirty = False
        for x in seq:
            self.append(x)

    def _mark_dirty(self, _):
        self._dirty = True

    def flush(self):
        self._refs = [x for x in self._refs if x() is not None]
        self._dirty = False

    def __eq__(self, other):

        return self is other

    def __getitem__(self, idx):
        if self._dirty:
            self.flush()
        if type(idx) == slice:
            return list(ref() for ref in self._refs[idx])
        return self._refs[idx]()

    def __iter__(self):
        if self._dirty:
            self.flush()
        for ref in self._refs:
            yield ref()

    def __repr__(self):
        return "WeakList(%r)" % list(self)

    def __str__(self):
        return "[{}]".format(", ".join(list((item.__str__() for item in list(self)))))

    def __len__(self):
        if self._dirty:
            self.flush()
        return len(self._refs)

    def __setitem__(self, idx, obj):
        if isinstance(idx, slice):
            self._refs[idx] = [ref(obj, self._mark_dirty) for _ in obj]
        else:
            self._refs[idx] = ref(obj, self._mark_dirty)

    def __delitem__(self, idx):
        del self._refs[idx]

    def append(self, obj):
        self._refs.append(ref(obj, self._mark_dirty))

    def count(self, obj):
        return list(self).count(obj)

    def extend(self, items):
        for x in items:
            self.append(x)

    def index(self, obj, **kwargs):
        return list(self).index(obj, **kwargs)

    def insert(self, idx, obj):
        self._refs.insert(idx, ref(obj, self._mark_dirty))

    def pop(self, *args, **kwargs):
        if self._dirty:
            self.flush()
        idx = args[0]
        obj = self._refs[idx]()
        del self._refs[idx]
        self.flush()
        return obj

    def remove(self, obj):
        if self._dirty:
            self.flush()  # Ensure all valid.
        for i, x in enumerate(self):
            if x == obj:
                del self[i]
        self.flush()

    def reverse(self):
        self._refs.reverse()

    def sort(self, key=None, reverse=False):
        if self._dirty:
            self.flush()
        if key is not None:
            key = lambda x, key=key: key(x())
        else:
            key = lambda x: x()
        self._refs.sort(key=key, reverse=reverse)

    def __add__(self, other):
        wl = WeakList(self)
        wl.extend(other)
        return wl

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __contains__(self, obj):
        return obj in list(self)

    def __mul__(self, n):
        return WeakList(list(self) * n)

    def __imul__(self, n):
        self._refs *= n
        return self

    def __reversed__(self):
        for ref in self._refs.__reversed__():
            yield ref()


class WeakTypedList(TypedList, WeakList):

    def __init__(self, *ItemsClass, seq=()):
        WeakList.__init__(self, seq=seq)
        TypedList.__init__(self, *ItemsClass)

    def __eq__(self, other):
        return self is other

    def __setitem__(self, index, p_object):
        self._check(p_object)

        WeakList.__setitem__(self, index, p_object)

    def __str__(self):
        return WeakList.__str__(self)

    def append(self, p_object):
        self._check(p_object)

        WeakList.append(self, p_object)

    def extend(self, iterable):
        for p_object in iterable:
            self.append(p_object)

    def insert(self, index, p_object):
        self._check(p_object)

        WeakList.insert(self, index, p_object)


class WeakTypedSet(WeakSet, TypedSet):
    """
    A TypedSet is a unordered collection of unique elements
    who can only contain items of type ItemsClass

    seq is the optionnal initial sequence

    WARNING : elements of a WeakTypedSet object are stored in WeakTypedSet.data
    """

    def __init__(self, ItemsClass, seq=()):

        WeakSet.__init__(self, data=seq)
        TypedSet.__init__(self, ItemsClass=ItemsClass)

    def __eq__(self, other):

        return self is other

    def __repr__(self):
        return super().__repr__()
        # return "<WeakTypedSet({}):{}>".format(self.ItemsClass.__name__, set.__str__(self))

    def __str__(self):
        return super().__str__()
        # return "{{}}".format(", ".join(list((item.__str__() for item in self))))

    def add(self, item):
        """
        Add an item to a set.
        This has no effect if the item is already present.

        :param item: an item of type self.ItemsClass
        :return: None
        """
        self._check(item)
        WeakSet.add(self, item)

    def update(self, *args):
        """
        Add all items from args into a set
        if the items already is in the set, it isn't added

        S.update({1, 2, 3})
        S.update({1}, {2}, {3})

        :param args: a sequence of items sequence
        :return: None
        """
        for seq in args:
            for item in seq:
                self.add(item)


def get_name(obj):
    for k, v in globals().items():
        if k == "obj":
            continue
        if v == obj:
            return k
    return None


def debug(func):
    functools.wraps(func)

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise e

    return wrapper
