
import math


class Position(tuple):
    def __init__(self, seq=()):
        tuple.__init__(seq)
        self.dim = len(seq)

    def __add__(self, other):
        if not isinstance(other, tuple):
            raise TypeError("position can only be added to another position")
        if self.dim != len(other):
            raise ValueError("positions have to be in the same dimension")
        return tuple(self[i] + other[i] for i in range(self.dim))

    def __mul__(self, n):
        if isinstance(n, int):
            return tuple(self[i] * n for i in range(self.dim))
        if not isinstance(n, tuple):
            raise TypeError("position can only be multiplied to integer or position")
        if self.dim != len(n):
            raise ValueError("positions have to be in the same dimension")
        return tuple(self[i] * n[i] for i in range(self.dim))


class Segment3(list):
    def __init__(self, liste_pnts):
        super().__init__(liste_pnts)

    length = property(lambda self: math.sqrt((self[1][0] - self[0][0]) ** 2 +
                                             (self[1][1] - self[0][1]) ** 2 +
                                             (self[1][2] - self[0][2]) ** 2))


class Vecteur(list):
    def __init__(self, x, y=None, add_vect=False, set_normalized=False):
        """
        Cree la somme des vecteurs donnes multiplies par leurs coefficients
        OU
        Cree un vecteur de composantes x, y, z
        OU
        Cree un vecteur allant du point x au point y
        OU
        Cree le vecteur allant de (0, 0, 0) au point x
        """
        # super permet de recuperer le __init__ d'un liste normale
        if add_vect:
            super().__init__((0, 0, 0))
            for coef, vect in x:
                for i in range(3):
                    self[i] += coef * vect[i]
        else:
            try:
                super().__init__((y[0] - x[0], y[1] - x[1], y[2] - x[2]))
            except TypeError:
                try:
                    super().__init__((x[0] * y, x[1] * y, x[2] * y))
                except TypeError:
                    try:
                        super().__init__((x[0], x[1], x[2]))
                    except IndexError:
                        try:
                            super().__init__((x[1][0] - x[0][0], x[1][1] - x[0][1], x[1][2] - x[0][2]))
                        except TypeError:
                            raise TypeError
                    except TypeError:
                        raise TypeError

        if set_normalized:
            self.normalize()

    norme = property(lambda self: math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2))

    # Sortir ces fonction de l'objet
    def produit_scal(self, vect):
        """Renvoi le produit scalaire de self par  vect"""
        return self[0] * vect[0] + self[1] * vect[1] + self[2] * vect[2]

    def produit_vect(self, vect):
        """Renvoi le produit vectoriel de self par  vect"""
        return Vecteur((self[1] * vect[2] - vect[1] * self[2],
                        self[2] * vect[0] - vect[2] * self[0],
                        self[0] * vect[1] - vect[0] * self[1]))

    def normalize(self):
        """Modifie self afin qu'il ait une norme de 1"""
        norme = self.norme
        for i in range(len(self)):
            self[i] /= norme

    def get_angle(self, vect, normed=False):
        """Renvoi l'angle qui separe les deux vecteurs
        Il est compris entre 0 et pi"""
        scal = self.produit_scal(vect)
        if normed:
            return math.acos(scal)
        else:
            return math.acos(scal / (self.norme * vect.norme))


class Base(list):
    def __init__(self, pos=(), v1=Vecteur, v2=Vecteur, v3=Vecteur):
        super(Base, self).__init__((pos, v1, v2, v3))
        self.origine = pos


class Plan:
    def __init__(self, origine, v1, v2):
        self._origine = origine  # Ne jamais utiliser _origine, toujours origine !
        self.v1 = v1
        self.v2 = v2
        self.v1.normalize()
        self.v_normal = v1.produit_vect(v2)
        self.v_normal.normalize()
        self.v2 = self.v_normal.produit_vect(self.v1)
        self.d = - (self.v_normal.produit_scal(self.origine))

    def update(self, v1, v2):
        self.__init__(self.origine, v1, v2)

    def set_origine(self, x):
        self._origine = x
        self.d = - self.v_normal.produit_scal(x)
    origine = property(lambda self: self._origine, set_origine)

    def contain(self, pnt, d=.0):  # Marche vraiment ? # UNUSED
        """Permet de savoir si un point est contenu dans le plan"""
        return abs(self.get_distance(pnt)) <= d

    def facing(self, pnt, d=.0):
        """Permet de savoir si le pnt est devant le plan avec une precision de d"""
        v = Vecteur(self.origine, pnt)
        rho = self.v_normal.produit_scal(v)
        """return self.v_normal[0] * (pnt[0] - self.origine[0])
             + self.v_normal[1] * (pnt[1] - self.origine[1])
             + self.v_normal[2] * (pnt[2] - self.origine[2]) > d"""
        return rho >= d

    def get_distance(self, pnt):
        return self.v_normal.produit_scal(Vecteur(self.origine, pnt))

    def intersection(self, pnt1, pnt2):  # CHERCHER UNE APPROCHE QUI PASSE PAR LES COORD DANS LE PLAN SELON v1 ET v2
        """Renvoi l'intersection entre self et la droite (pnt1, pnt2)
        3 cas:
         - L'intersection est un unique point (renvoi ce point)
         - La droite est confondue dans le plan (renvoi la droite)
         - La droite est parallele au plan (renvoi none)"""

        v = Vecteur(pnt1, pnt2)

        v_normal = self.v_normal
        rho = v_normal.produit_scal(v)

        if rho:
            # P = D <=> a * (x1 + vx * k) + b * (y1 + vy * k) + c * (z1 + vz * k) + d = 0
            #       <=> k [ a*vx + b*vy + c*vz ] = - [ a*x1 + b*y1 + c*z1 + d ]
            #       <=> k [ v_normal.produit_scal(v) ] = - [ v_normal.produit_scal(p1) + d ]   Car (a b c) = v_normal
            #       <=> k = - ( v_normal.produit_scal(p1) + d ) / v_normal.produit_scal(v)

            k = - (v_normal.produit_scal(pnt1) + self.d) / rho
            # k est le pourcentage de distance a parcourir en partant de pnt1 en suivant le vecteur v
            # k "s'arrete" a l'intersection entre le plan et la droite
            # Si pnt1 et pnt2 ne sont pas du mm cote de l'ecran, 0 <= k <= 1

            if self.facing(pnt1) == self.facing(pnt2):
                print("PROBLEME : Les deux pnts sont du mm cote du plan")

            if not (0 <= k <= 1):
                if not (0 <= arrondir(k, .0000001) <= 1):
                    print("\nON EST DEHORS !!!!!"
                          "\n  Avancement k = {}"
                          "\n  Rho = {}"
                          "\n  v_normal.produit_scal(pnt1) + d = {}"
                          "\n  v_normal.produit_scal(pnt2) + d = {}"
                          "\n  Dis(pnt1) + d = {}"
                          "\n  Dis(pnt2) + d = {}"
                          "\n  Pnt1 = {}"
                          "\n  Pnt2 = {}"
                          "\n  Facing1 = {}"
                          "\n  Facing2 = {}"
                          "\n  d = {}"
                          "".format(k, rho, v_normal.produit_scal(pnt1) + self.d, v_normal.produit_scal(pnt2) + self.d,
                                    self.get_distance(pnt1), self.get_distance(pnt2),
                                    pnt1, pnt2, self.facing(pnt1), self.facing(pnt2), self.d))

                k = arrondir(k, .0000001)

            # On part de pnt1 et on avance de k fois le vecteur pnt1 -> pnt2 pour arriver sur le plan
            av = (1, pnt1), (k, v)
            intersect = tuple(Vecteur(av, add_vect=True))

            if not self.facing(intersect, -.005):
                print("\nL'intersection trouvee est derriere le plan"
                      "\n  Pnt1 = {}"
                      "\n  Pnt2 = {}"
                      "\n  k = {}"
                      "\n  Intersect = {}"
                      "\n  Rho = {}"
                      "\n  Facing -.005 = {}"
                      "".format(pnt1, pnt2, k, intersect, self.get_distance(intersect),
                                self.facing(intersect, -.005)))
            return intersect
        else:
            # La droite est parallele a l'ecran
            # Dans ce projet, cela est une erreur,
            # car cette fonction est appelee seulement si un pnt est devant et l'autre derriere le plan
            print("\nL'intersection est nulle !!!!!"
                  "\n  Vecteur normal du plan = {}"
                  "\n  Vecteur de la droite = {}"
                  "\n  Rho = {}"
                  "\n  Pnt1 = {}"
                  "\n  Pnt2 = {}"
                  "\n  Facing1 = {}"
                  "\n  Facing2 = {}"
                  "".format(v_normal, v, rho, pnt1, pnt2, self.facing(pnt1), self.facing(pnt2)))

            return None


class Sphere:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def get_proj(self, pnt):
        v = Vecteur(self.center, pnt)
        k = self.radius / v.norme
        av = (1, self.center), (k, v)
        return tuple(Vecteur(av, add_vect=True))


class Polygon2(list):
    """Cree un polygone en 2D"""
    def __init__(self, liste_pnts=None):
        if liste_pnts is None:
            liste_pnts = []
        super().__init__(liste_pnts)
        for i in range(len(self)):
            self[i] = arrondir_pnt(self[i])  # , .01)

    def get_rect(self):
        """Renvoi un tuple contenant les donnees d'un rectangle"""
        left, top = self[0]
        right, bottom = left, top
        for x, y in self:
            if left > x:
                left = x
            elif right < x:
                right = x
            if top > y:
                top = y
            elif bottom < y:
                bottom = y
        return left, top, right - left, bottom - top
    rect = property(get_rect)


class Polygon3(list):
    """Cree un polygone en 3D"""
    def __init__(self, liste_pnts=None):
        if liste_pnts is None:
            liste_pnts = []
        super().__init__(liste_pnts)


def arrondir_pnt(pnt, d=1):
    return tuple([arrondir(pnt[i], d) for i in range(len(pnt))])

def arrondir(x, d=1):
    return round(x / d) * d
