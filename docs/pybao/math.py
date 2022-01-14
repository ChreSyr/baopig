
def combinliste(seq, k):
    p = []
    i, imax = 0, 2 ** len(seq) - 1
    # print(imax)
    while i <= imax:
        s = []
        j, jmax = 0, len(seq) - 1
        while j <= jmax:
            if (i >> j) & 1 == 1:
                s.append(seq[j])
            j += 1
        if len(s) == k:
            p.append(s)
        i += 1
    return p

def combinindexliste(seq, k):
    p = []
    i, imax = 0, 2 ** len(seq) - 1
    # print(imax)
    while i <= imax:
        s = []
        j, jmax = 0, len(seq) - 1
        while j <= jmax:
            if (i >> j) & 1 == 1:
                s.append(j)
            j += 1
        if len(s) == k:
            p.append(s)
        i += 1
    return p

def get_decomp_produit_fact_premiers(x):

    if x is 1:
        return []

    decomp = []
    nombres_premiers = get_nombres_premiers(int(x / 2))
    for n in nombres_premiers:
        if divide(n, x):
            x = int(x / n)
            decomp = get_decomp_produit_fact_premiers(x)
            decomp.append(n)
            break

    if not decomp:
        return [x]

    return decomp

def get_nombres_premiers(x):
    """
    Renvoi la liste des nombres premiers inferieur ou egal a x
    :param x: Valeur plafond
    :return: tuple de nombres premiers
    """
    numbers = tuple(x for x in range(2, x + 1))
    nombres_premiers = []

    for i in range(len(numbers)):
        if True not in (divide(numbers[j], numbers[i]) for j in range(i)):
            nombres_premiers.append(numbers[i])

    return tuple(nombres_premiers)

def divide(p, x):
    """
    Function who check if p divide x
    :param p: The number who divide
    :param x: The number to divide
    :return: True if p divide x else False
    """
    return x % p == 0

def mult_list(x):
    if len(x) == 1:
        return x[0]

    return x[0] * mult_list(x[1:])

def sum_tuple(*args, **kwargs):
    return tuple(sum(args[j][i] * kwargs['k' + str(j)]
                     if kwargs.get('k' + str(j)) else args[j][i]
                     for j in range(len(args)))
                 for i in range(len(args[0])))


nombre_or = 1.618033988749895
