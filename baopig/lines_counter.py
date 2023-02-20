import os

path = os.path.abspath(__file__)[:-16]

list_of_files = {}
for (dirpath, dirnames, filenames) in os.walk(path):
    for filename in filenames:
        if filename.endswith('.py'):
            list_of_files[filename] = os.sep.join([dirpath, filename])

lines = 0
for item in list_of_files.items():
    print(item, end=' lines:')
    with open(item[1], 'r', encoding="utf-8") as reader:
        l = len(reader.readlines())
        print(l)
        lines += l
print(f"Baopig is currently made of {lines} lines of python code.")
