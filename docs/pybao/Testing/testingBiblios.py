
from pybao.ObjectUtilities import TypedList, TypedSet, TypedDict, TypedDeque

l = TypedList(str, "FIRST")
# l.append(36)
l.append("test")
l.extend(["1", "2"])
l.insert(7, "1.5")
l.__setitem__(5, "test2")
print(l)

s = TypedSet(int, {5, 6})
# s.add("yolo")
s.add(0)
s.update({1, 2}, {1, 2}, {3, 4})
print(s)

d = TypedDict(str, int)
# d["combien ?"] = "trent-six"
d["zero"] = 0
d.setdefault("un", 1)
d.setdefault("deux", 1)
d.setdefault("deux")
d2 = {"trois":3}
d2.update({"quatre":4})
d.update(d2)
d.update(cinq=5, six=6, sept=7)
d.update()
print(d)
d3 = TypedDict(int, str, {1:"un", 2:"deux"})
print(d3)

d = TypedDeque(int, maxlen=5)
d.append(3)
d.extend({4, 6})
d.appendleft(2)
d.extendleft([1, 0])
try:
    d.insert(4, 5)
    raise AssertionError
except IndexError:
    pass
d.__setitem__(0, 10)
d[1] = 100
# d.append("3")
# d.extend({"4", 6})
# d.appendleft("2")
# d.extendleft(["1", 0])
# d.insert(4, "5")
# d.__setitem__(0, "10")
# d[1] = "100"
print(d)


