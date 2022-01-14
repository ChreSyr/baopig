
import inspect
import threading
from collections import deque
from weakref import ref as wkref, WeakSet, WeakValueDictionary
import functools


class AcceptError(PermissionError): pass


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
    def __init__(self, dict=None, **kwargs):
        if dict is None:
            dict = kwargs.items()
        for key, value in dict:
            self.__setattr__(key, value)

    def __str__(self) -> str:
        return "<{}({})>".format(self.__class__.__name__, str(self.__dict__)[1:-1])


class EditableTuple:
    """
    An EditableTuple has a fixed length but its elements can be changed

    WARNING : an EditableTuple is not a tuple instance
    """

    def __init__(self, tup):

        self._tup = tuple(tup)
    def __contains__(self, key):
        """ Return key in self. """
        return self._tup.__contains__(key)

    def __eq__(self, value):
        """ Return self==value. """
        return self._tup.__eq__(value)

    def __ge__(self, value):
        """ Return self>=value. """
        return self._tup.__ge__(value)

    def __getitem__(self, key):
        """ Return self[key]. """
        return self._tup.__getitem__(key)

    def __gt__(self, value):
        """ Return self>value. """
        return self._tup.__gt__(value)

    def __hash__(self):
        """ Return hash(self). """
        return self._tup.__hash__()

    def __iter__(self):
        """ Implement iter(self). """
        return self._tup.__iter__()

    def __len__(self):
        """ Return len(self). """
        return self._tup.__len__()

    def __le__(self, value):
        """ Return self<=value. """
        return self._tup.__le__(value)

    def __lt__(self, value):
        """ Return self<value. """
        return self._tup.__lt__(value)

    def __ne__(self, value):
        """ Return self!=value. """
        return self._tup.__ne__(value)

    def __repr__(self):
        """ Return repr(self). """
        return self._tup.__repr__()

    def __setitem__(self, key, value):
        """ Set self[key] to value. """

        change = lambda k, v: value if k == key else v
        # tup = tuple([change(k, v) for k, v in enumerate(self._tup)])
        # if tup == self._tup:
        #     raise IndexError("tuple index out of range (given index : %s)" % key)
        self._tup = tuple([change(k, v) for k, v in enumerate(self._tup)])

    def __str__(self):
        """ Return str(self). """
        return self._tup.__str__()

    def count(self, value):
        """ T.count(value) -> integer -- return number of occurrences of value """
        return self._tup.count(value)

    def index(self, value, start=None, stop=None):
        """
        T.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present.
        """
        return self._tup.index(value, start, stop)


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
        return "[{}]".format(", ".join(list((item.__str__() for item in self)))) + (", maxlen={}".format(self.maxlen) if self.maxlen else "")

    def _check(self, p_object):
        if not self.accept(p_object):
            raise AcceptError(self.msg_item_type_error)

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


class TypedDict(dict):
    def __init__(self, KeysClass, ValuesClass, seq={}, **kwargs):
        """
        Create a dict who can only contain keys of type keys_class
        and values of type values_class

        :param KeysClass: the type for all dict keys
        :type KeysClass: class
        :param ValuesClass: the type for all dict values
        :type ValuesClass: class
        :param seq: an items sequence
        :param kwargs: an items dictionnary
        """
        assert inspect.isclass(KeysClass), "KeysClass must be a class"
        assert inspect.isclass(ValuesClass), "ValuesClass must be a class"
        assert isinstance(seq, dict), "Optionnal seq must be a dictionnary"

        self.KeysClass = KeysClass
        self.ValuesClass = ValuesClass
        self.msg_key_type_error = "Only {} objects are accepted as key in this dict" \
                                  "".format(self.KeysClass.__name__)
        self.msg_value_type_error = "Only {} objects are accepted as value in this dict" \
                                    "".format(self.ValuesClass.__name__)

        for key, value in seq.items():
            self._checkkey(key)
            self._checkvalue(value)
        dict.__init__(self, seq, **kwargs)

    def __setitem__(self, *args, **kwargs):
        try:
            self._checkkey(args[0])
            self._checkvalue(args[1])
            dict.__setitem__(self, *args, **kwargs)
        except Exception as e:
            raise Exception("This method is not properly coded, " + str(e))

    def __repr__(self):
        return "<TypedDict({}, {}):{}>" \
               "".format(self.KeysClass.__name__, self.ValuesClass.__name__, dict.__str__(self))

    def __str__(self):
        return "{"+", ".join("{}:{}".format(i, o) for i, o in self.__dict__.items())+"}"

    def _checkkey(self, key):
        if not self.acceptkey(key):
            raise AcceptError(self.msg_key_type_error)

    def _checkvalue(self, value):
        if not self.acceptvalue(value):
            raise AcceptError(self.msg_value_type_error)

    def acceptkey(self, item):
        return isinstance(item, self.KeysClass)

    def acceptvalue(self, item):
        return isinstance(item, self.ValuesClass)

    def setdefault(self, k, d=None):
        """
        If k not in D: set D[k]=d
        If d is None:  set d=D.ValuesClass()
        Return D[k]

        WARNING: ValuesClass might need arguments

        :param k: a key
        :param d: the key value if key isn't in the dict yet
        :return: D[k]
        """
        if d is None:
            d = self.ValuesClass()

        self._checkkey(k)
        self._checkvalue(v)

        return dict.setdefault(self, k, d)

    def update(self, E=None, **F):
        """
        Set D[k] = v for k, v in E.items() or F.items()

        D.update(key1=1, key2=2) <=> D.update({'key1':1, 'key2':2})

        :param E: a dictionnary
        :param F: optionnal - a dictionnary (made by keywords)
        :return: None
        """
        if E is None:
            E = F
        assert isinstance(E, dict), "E must be a dictionnary"

        for k, v in E.items():
            self[k] = v


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
            raise AcceptError(self.msg_item_type_error.format(item.__class__.__name__))

    def accept(self, item):
        # print("accept", item.__class__.__name__, self.ItemsClass_name, isinstance(item, self.ItemsClass))
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
            self._check(p_object)


class SortedTypedList(TypedList):
    """
    Create an list of Focusable components ordered by there positions
    """

    def __init__(self, *ItemsClass, sort_key, seq=()):

        TypedList.__init__(self, *ItemsClass, seq)
        self._sort_key = sort_key

    def accept(self, item):
        return hasattr(item, self._sort_key) and super().accept(item)

    def append(self, item):
        assert item not in self

        item_key = getattr(item, self._sort_key)
        for i, item2 in enumerate(self):
            item2_key = getattr(item2, self._sort_key)
            if item_key < item2_key:
                super().insert(i, item)
                break
        if not item in self:
            super().append(item)

        assert list(self) == sorted(self, key=lambda o: getattr(o, self._sort_key))

    def insert(self, index, comp):
        raise PermissionError("Cannot insert item on a sorted list")

    def sort(self):
        super().sort(key=lambda o: getattr(o, self._sort_key))


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
            raise AcceptError(self.msg_item_type_error)

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


class History(TypedDeque):
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

    def __init__(self, ItemsClass, maxlen, seq=()):
        TypedDeque.__init__(self, ItemsClass, seq, maxlen)

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
        self._dirty=False
        for x in seq: self.append(x)

    def _mark_dirty(self, wref):
        self._dirty = True

    def flush(self):
        self._refs = [x for x in self._refs if x() is not None]
        self._dirty=False

    def __eq__(self, other):

        return self is other

    def __getitem__(self, idx):
        if self._dirty: self.flush()
        if type(idx) == slice:
            return list(ref() for ref in self._refs[idx])
        return self._refs[idx]()

    def __iter__(self):
        if self._dirty: self.flush()
        for ref in self._refs:
            yield ref()

    def __repr__(self):
        return "WeakList(%r)" % list(self)

    def __str__(self):
        return "[{}]".format(", ".join(list((item.__str__() for item in list(self)))))

    def __len__(self):
        if self._dirty: self.flush()
        return len(self._refs)

    def __setitem__(self, idx, obj):
        if isinstance(idx, slice):
            self._refs[idx] = [ref(obj, self._mark_dirty) for x in obj]
        else:
            self._refs[idx] = ref(obj, self._mark_dirty)

    def __delitem__(self, idx):
        del self._refs[idx]

    def append(self, obj):
        self._refs.append(ref(obj, self._mark_dirty))

    def count(self, obj):
        return list(self).count(obj)

    def extend(self, items):
        for x in items: self.append(x)

    def index(self, obj):
        return list(self).index(obj)

    def insert(self, idx, obj):
        self._refs.insert(idx, ref(obj, self._mark_dirty))

    def pop(self, idx):
        if self._dirty: self.flush()
        obj=self._refs[idx]()
        del self._refs[idx]
        self.flush()
        return obj

    def remove(self, obj):
        if self._dirty: self.flush() # Ensure all valid.
        for i, x in enumerate(self):
            if x == obj:
                del self[i]
        self.flush()

    def reverse(self):
        self._refs.reverse()

    def sort(self, key=None, reverse=False):
        if self._dirty: self.flush()
        if key is not None:
            key = lambda x, key=key: key(x())
        else:
            key = lambda x: x()
        self._refs.sort(key=key, reverse=reverse)

    def __add__(self, other):
        l = WeakList(self)
        l.extend(other)
        return l

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __contains__(self, obj):
        return obj in list(self)

    def __mul__(self, n):
        return WeakList(list(self)*n)

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


class WeakSortedTypedList_TBR(WeakTypedList):
    """
    Create an list of Focusable components ordered by a key
    WARNING : the list will be sorted after an append(elt) and after a sort(),
              but it is not updating in real-time
    """
    # TODO : remove this class, because it creates logic issues (we think the list is always sorted but it's not)

    def __init__(self, *ItemsClass, key=None, seq=()):

        WeakTypedList.__init__(self, *ItemsClass, seq)
        self._key = key
        if key is not None:
            def cannot_insert(index, p_object):
                raise PermissionError("Cannot insert item on a sorted list")
            self.insert = cannot_insert

    def append(self, item):
        assert item not in self

        super().append(item)
        if self._key is not None:
            self.sort()

    def sort(self):
        if self._dirty: self.flush()
        if self._key is not None:
            super().sort(key=self._key)
        else:
            super().sort()


""" --- Unit tests for WeakList and WeakTypedList ---

class Obj:
    def __init__(self, num):
        self.id = num
    def __str__(self):
        return "Obj(%s)" % self.id


weak_list = WeakList()
weak_list2 = WeakList()
strong_list = []
weak_typed_list = WeakTypedList(ItemsClass=Obj)

weak_typed_list.append(Obj(4))
assert len(weak_typed_list) == 0

for i in range(4):
    obj = Obj(i)
    strong_list.append(obj)
    weak_list.append(obj)
    weak_list2.append(obj)
    weak_typed_list.append(obj)

print(weak_list)
print(len(weak_list))
assert len(weak_list) == 4

del strong_list[2]
assert len(weak_list) == 3
for obj in weak_list:
    print(obj)
print(weak_list, weak_list2, weak_typed_list)
print(strong_list)
"""

"""
# --- Unit tests for WeakSet and WeakTypedSet ---

class Obj:
    def __init__(self, num):
        self.id = num
    def __str__(self):
        return "Obj(%s)" % self.id
    def __del__(self):
        print("DELETE : " + str(self))


obj = Obj(3)
weak_set = WeakSet()
weak_typed_set = WeakTypedSet(Obj)

weak_set.add(obj)
weak_typed_set.add(obj)

print("weak_set :", weak_set)
print("weak_typed_set :", weak_typed_set)
del obj
print("weak_set", weak_set)
print("weak_typed_set :", weak_typed_set)
"""

def get_name(obj):
    for k, v in globals().items():
        if k == "obj":
            continue
        if v == obj:
            return k
    return None

    """ --- get_name testing ---
    abc = 3
    print(get_name(abc))
    """


def debug(func):
    functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise e
    return wrapper

