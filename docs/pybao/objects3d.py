
import math
from biblios.BiblioEspacesVect import Segment3, Vecteur, Sphere, Polygon3, arrondir_pnt
from biblios.BiblioErrors import MustBePositive
from biblios.BiblioMath import nombre_or, combinliste, get_decomp_produit_fact_premiers

# Pour les tests
from biblios.BiblioFunctionsEV import fc


class Object3D:
    def __init__(self):
        self.vertexes = None
        self.triangles = None


class Polygon(Object3D):
    def __init__(self, liste_pnts, color=(255, 255, 255)):
        super().__init__()

        origine = liste_pnts[0]
        self.vertexes = liste_pnts
        self.triangles = []
        for i in range(len(liste_pnts) - 2):
            self.triangles.append(Triangle((origine, liste_pnts[i + 1], liste_pnts[i + 2]), color))


class ConvexPolyhedron(Object3D):
    def __init__(self, center, pnts, color, intern_radius=.0):
        super().__init__()

        self.center = center
        liste_pnts = tuple(tuple((round(coord) for coord in pnt)) for pnt in pnts)
        self.vertexes = liste_pnts
        self.triangles = []
        self.color = color

        combinaisons = combinliste(liste_pnts, 3)
        for combin in combinaisons:

            triangle1 = Triangle((combin[0], combin[1], combin[2]), color)
            if not triangle1.facing_point(self.center, -intern_radius):
                if True not in (triangle1.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle1):
                    self.triangles.append(triangle1)

            triangle2 = Triangle((combin[0], combin[2], combin[1]), color)
            if not triangle2.facing_point(self.center, -intern_radius):
                if True not in (triangle2.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle2):
                    self.triangles.append(triangle2)


class Pyramide(ConvexPolyhedron):
    def __init__(self, x, y, z, direction, color=(0, 255, 0)):

        self.dir = direction * math.pi/2
        cos = math.cos(self.dir)
        sin = math.sin(self.dir)
        origine = x_top, y_top, z_top = x, y, z - 50 * sin  # Pointe de la pyramide

        vertexes = (origine,
                    (x_top + cos * 50, y_top - 50, z_top + sin * 50),
                    (x_top-sin*25, y_top-50, z_top+cos*25),
                    (x_top+sin*25, y_top-50, z_top-cos*25))
        super().__init__(origine, vertexes, color)


class PyramideBackUp(Object3D):
    def __init__(self, x, y, z, dir):
        super().__init__()

        self.dir = dir * math.pi/2
        cos = math.cos(self.dir)
        sin = math.sin(self.dir)
        origine = x_top, y_top, z_top = x, y, z - 50 * sin  # Pointe de la pyramide

        self.vertexes = (origine,
                         (x_top+cos*50, y_top-50, z_top+sin*50),
                         (x_top-sin*25, y_top-50, z_top+cos*25),
                         (x_top+sin*25, y_top-50, z_top-cos*25))
        self.triangles = (Triangle([self.vertexes[i] for i in (1, 2, 3)], (0, 255, 0)),
                          Triangle([self.vertexes[i] for i in (0, 2, 1)], (0, 255, 0)),
                          Triangle([self.vertexes[i] for i in (0, 3, 2)], (0, 255, 0)),
                          Triangle([self.vertexes[i] for i in (0, 1, 3)], (0, 255, 0)))


class BlocTestWrong(ConvexPolyhedron):
    def __init__(self, x, y, z):

        vertexes = ((x, y, z),
                    (x + 50, y, z),
                    (x + 50, y, z + 50),
                    (x, y, z + 50),
                    (x, y + 50, z),
                    (x + 50, y + 50, z),
                    (x + 50, y + 50, z + 50),
                    (x, y + 50, z + 50))
        super().__init__(vertexes)


class Bloc(Object3D):
    def __init__(self, x, y, z, w=50, color=(255, 255, 255)):
        super().__init__()

        self.vertexes = ((x, y, z),
                         (x + w, y, z),
                         (x + w, y, z + w),
                         (x, y, z + w),
                         (x, y + w, z),
                         (x + w, y + w, z),
                         (x + w, y + w, z + w),
                         (x, y + w, z + w))
        self.triangles = (Triangle([self.vertexes[i] for i in (0, 1, 2)], color),
                          Triangle([self.vertexes[i] for i in (0, 2, 3)], color),
                          Triangle([self.vertexes[i] for i in (7, 6, 5)], color),
                          Triangle([self.vertexes[i] for i in (7, 5, 4)], color),
                          Triangle([self.vertexes[i] for i in (0, 3, 7)], color),
                          Triangle([self.vertexes[i] for i in (0, 7, 4)], color),
                          Triangle([self.vertexes[i] for i in (1, 5, 6)], color),
                          Triangle([self.vertexes[i] for i in (1, 6, 2)], color),
                          Triangle([self.vertexes[i] for i in (0, 4, 5)], color),
                          Triangle([self.vertexes[i] for i in (0, 5, 1)], color),
                          Triangle([self.vertexes[i] for i in (3, 2, 6)], color),
                          Triangle([self.vertexes[i] for i in (3, 6, 7)], color))


class ConvexRegularIcosahedron(ConvexPolyhedron):
    def __init__(self, center, radius, color=(255, 255, 255)):

        self.radius = radius

        x, y, z = center
        pnts = []
        nombre_de_cotes = 5
        taille_cote = 2 * radius / math.sqrt(2 + nombre_or)

        # s est le demi-perimetre du triangle isocele (radius, radius, cote)
        s = (radius + radius + taille_cote) / 2
        a = (s - radius) * math.sqrt(s * (s - taille_cote))
        h = 2 * a / radius
        h2 = math.sqrt(taille_cote ** 2 - h ** 2)
        self.intern_radius = h2

        pnts.append((x, y, z + radius))

        for i in range(nombre_de_cotes):
            pnts.append((x - h * math.sin(i * 2 * math.pi / nombre_de_cotes),
                         y + h * math.cos(i * 2 * math.pi / nombre_de_cotes),
                         z + radius - h2))

        for i in range(nombre_de_cotes):
            pnts.append((x + h * math.sin(i * 2 * math.pi / nombre_de_cotes),
                         y - h * math.cos(i * 2 * math.pi / nombre_de_cotes),
                         z - radius + h2))

        pnts.append((x, y, z - radius))

        super().__init__(center, pnts, color, intern_radius=h2)

        # affichage infos
        if False:
            print("Rayon =", radius)
            print("Taille cote =", taille_cote)
            print("Demi-perim = ", s)
            print("Aire = ", a)
            print("Hauteur :", h)
            print("Hauteur2 :", h2)
            for tr in self.triangles:
                print(fc.distance(tr[0], tr[1]))
                print(fc.distance(tr[2], tr[1]))
                print(fc.distance(tr[0], tr[2]))


class Geode5Test(ConvexRegularIcosahedron):
    def __init__(self, center, radius, a=1, b=0, color=(255, 255, 255)):
        super().__init__(center, radius, color)

        self.sphere = Sphere(center, radius)

        triangles = self.triangles.copy()
        self.triangles.clear()
        for triangle in triangles:

            liste_pnts = self.get_points_of_littles_triangles_from_triangle(triangle, a, b)

            self.triangles += self.get_triangles_from_points(liste_pnts)

            # break

    def get_little_triangles_from_list_triangles(self, triangles, a=1, b=0):
        if a is 1:
            return triangles

        full_littles_triangles = []
        facteurs_premiers = get_decomp_produit_fact_premiers(a)
        a2 = int(a / facteurs_premiers[0])
        for triangle in triangles:

            liste_pnts = self.get_points_of_littles_triangles_from_triangle(triangle, facteurs_premiers[0], b)
            littles_triangles = self.get_triangles_from_points(liste_pnts)

            littles_triangles = self.get_little_triangles_from_list_triangles(littles_triangles, a2, b)
            for little_triangle in littles_triangles:
                full_littles_triangles.append(little_triangle)

        return full_littles_triangles

    def get_points_of_littles_triangles_from_triangle(self, triangle, a=2, b=0):

        pa, pb, pc = triangle
        ab = Vecteur(pa, pb)
        ac = Vecteur(pa, pc)
        bc = Vecteur(pb, pc)
        taille_cote = ab.norme

        u = Vecteur(ab, 1 / (a + b))
        v = Vecteur(ac, 1 / (a + b))
        w = Vecteur(bc, 1 / (a + b))

        c = taille_cote / math.sqrt(a ** 2 + a * b + b ** 2)

        ava = (1, ab), (a, w)
        vect_e_a = Vecteur(ava, add_vect=True)
        norme = vect_e_a.norme
        for i in range(3):
            vect_e_a[i] *= c / norme

        avb = (1, ab), (-b, v)
        vect_e_b = Vecteur(avb, add_vect=True)
        norme = vect_e_b.norme
        for i in range(3):
            vect_e_b[i] *= c / norme

        # vect_e_a et vect_e_b ont maintenant la mm norme

        """print(vect_e_a.norme, vect_e_b.norme)
        print("Triangle : {}\n"
              "k : {}\n"
              "a : {}\n"
              "b : {}\n"
              "ab : {}\n"
              "ac : {}\n"
              "cb : {}\n"
              "u : {}\n"
              "v : {}\n"
              "w : {}\n"
              "Vect e_a : {}\n"
              "Vect e_b : {}".format(triangle, k, a, b, ab, ac, bc, u, v, w, vect_e_a, vect_e_b))"""

        # On cherche les x, y tq vect_e_a * x + vect_e_a * y inclus dans ABC
        # 0 <= y <= a
        # -a <= x <= 0

        # alpha = b / (a + b)
        above_ac = lambda x, y: (b / (a + b)) * x <= y
        # alpha = a / b
        under_ab = lambda x, y: y <= a / b * x if b else True
        # alpha = - ((a + b) / a)
        # beta = (a ** 2 + a * b + b ** 2) / a
        under_bc = lambda x, y: y <= - ((a + b) / a) * x + (a ** 2 + a * b + b ** 2) / a

        liste_pnts = list(triangle)
        for x in range(a + b + 1):
            for y in range(-b, a + 1):
                # print(x, y)

                if (x, y) in ((0, 0), (b, a), (a + b, -b)):  # if it's A, B or C
                    pass

                elif above_ac(x, y) and under_ab(x, y) and under_bc(x, y):
                        av = (1, pa), (x, vect_e_a), (y, vect_e_b)
                        pnt = tuple(Vecteur(av, add_vect=True))
                        proj = self.sphere.get_proj(pnt)
                        liste_pnts.append(proj)

        return liste_pnts

    def get_triangles_from_points(self, liste_pnts):

        # Pour chaque point
        # On cherche les points les plus proches
        # On en fait des triangles presque equilateraux

        for i, pnt1 in enumerate(liste_pnts):
            for j in range(1, len(liste_pnts) - i):
                pnt2 = liste_pnts[i + j]
                seg = Segment3((pnt1, pnt2))

        triangles = []

        combinaisons = combinliste(liste_pnts, 3)

        for combin in combinaisons:

            triangle1 = Triangle(combin, self.color)
            if not triangle1.facing_point(self.center, -self.intern_radius):
                if True not in (triangle1.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle1):
                    triangles.append(triangle1)

            else:
                triangle2 = Triangle((combin[0], combin[2], combin[1]), self.color)
                if not triangle2.facing_point(self.center, -self.intern_radius):
                    if True not in (triangle2.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle2):
                        triangles.append(triangle2)

        return triangles


class Geode5(ConvexRegularIcosahedron):
    def __init__(self, center, radius, a=1, color=(255, 255, 255)):
        super().__init__(center, radius, color)

        self.sphere = Sphere(center, radius)

        self.triangles = self.get_little_triangles_from_list_triangles(self.triangles, a)

    def get_little_triangles_from_list_triangles(self, triangles, x):
        if x is 1:
            return triangles

        full_littles_triangles = []
        facteurs_premiers = get_decomp_produit_fact_premiers(x)
        x2 = int(x / facteurs_premiers[0])
        for triangle in triangles:

            liste_pnts = self.get_points_of_littles_triangles_from_triangle(triangle, facteurs_premiers[0])
            littles_triangles = self.get_triangles_from_points(liste_pnts)

            littles_triangles = self.get_little_triangles_from_list_triangles(littles_triangles, x2)
            for little_triangle in littles_triangles:
                full_littles_triangles.append(little_triangle)

        return full_littles_triangles

    def get_points_of_littles_triangles_from_triangle(self, triangle, a=2):
        pa, pb, pc = triangle
        ab = Vecteur(pa, pb)
        ac = Vecteur(pa, pc)
        bc = Vecteur(pb, pc)
        taille_cote = ab.norme

        u = ab
        v = ac
        w = bc

        c = taille_cote / a

        vect_e_a = Vecteur(pa, pc)  # AC
        vect_e_b = Vecteur(pa, pb)  # AB

        for i in range(3):
            vect_e_a[i] /= a

        for i in range(3):
            vect_e_b[i] /= a

        # On cherche les x, y tq vect_e_a * x + vect_e_a * y inclus dans ABC
        # 0 <= y <= a
        # -a <= x <= 0

        f_test = lambda x: - x + a

        liste_pnts = list(triangle)
        for y in range(a + 1):
            for x in range(a + 1):

                d = 0
                if y <= f_test(x) + d:

                    av = (1, pa), (x, vect_e_a), (y, vect_e_b)
                    pnt = tuple(Vecteur(av, add_vect=True))
                    proj = self.sphere.get_proj(pnt)
                    proj = arrondir_pnt(proj)
                    if proj not in liste_pnts:
                        liste_pnts.append(proj)

        return liste_pnts

    def get_triangles_from_points(self, liste_pnts):

        triangles = []

        combinaisons = combinliste(liste_pnts, 3)

        for combin in combinaisons:
            triangle1 = Triangle(combin, self.color)
            if not triangle1.facing_point(self.center, -self.intern_radius):
                if True not in (triangle1.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle1):
                    triangles.append(triangle1)

            else:
                triangle2 = Triangle((combin[0], combin[2], combin[1]), self.color)
                if not triangle2.facing_point(self.center, -self.intern_radius):
                    if True not in (triangle2.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle2):
                        triangles.append(triangle2)

        return triangles


class Geode5Backup(ConvexRegularIcosahedron):
    def __init__(self, center, radius, a=1, b=0, color=(255, 255, 255)):
        super().__init__(center, radius, color)

        sphere = Sphere(center, radius)

        triangles = self.triangles.copy()
        for triangle in triangles:
            pa, pb, pc = triangle
            projs = list(triangle)
            segments = Segment3((pa, pb)), Segment3((pb, pc)), Segment3((pc, pa))
            for segment in segments:
                for i in range(a + b):
                    if i not in (0, a + b):
                        av = (1, segment[0]), (i / (a + b), Vecteur(segment[0], segment[1]))
                        pnt = Vecteur(av, add_vect=True)
                        proj = sphere.get_proj(pnt)
                        proj = arrondir_pnt(proj)
                        if proj not in projs:
                            projs.append(proj)

            liste_pnts = projs

            combinaisons = combinliste(liste_pnts, 3)
            self.triangles.remove(triangle)

            for combin in combinaisons:

                triangle1 = Triangle((combin[0], combin[1], combin[2]), color)
                if not triangle1.facing_point(self.center, -self.intern_radius):
                    if True not in (triangle1.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle1):
                        self.triangles.append(triangle1)

                triangle2 = Triangle((combin[0], combin[2], combin[1]), color)
                if not triangle2.facing_point(self.center, -self.intern_radius):
                    if True not in (triangle2.facing_point(pnt) for pnt in liste_pnts if pnt not in triangle2):
                        self.triangles.append(triangle2)
            # """


class Triangle(Polygon3):
    """Cree un polygone a trois sommets"""
    def __init__(self, liste_pnts, color=(255, 255, 255)):
        super(Triangle, self).__init__(liste_pnts)

        # Creation de la base
        self.origine = liste_pnts[0]
        v1 = Vecteur(self.origine, liste_pnts[1], set_normalized=True)
        v2 = Vecteur(self.origine, liste_pnts[2], set_normalized=True)
        self.v_normal = v1.produit_vect(v2)
        self.v_normal.normalize()

        # Couleur
        self.original_color = color
        self.color = list(color)

    def facing_point(self, pnt, d=.0):
        """Permet de savoir si le joueur est du bon cote de la face"""
        # return self.v_normal.produit_scal(Vecteur(self.base.origine, player.pos)) > d
        return self.v_normal[0] * (pnt[0] - self.origine[0]) \
             + self.v_normal[1] * (pnt[1] - self.origine[1]) \
             + self.v_normal[2] * (pnt[2] - self.origine[2]) > d

    def contains_point(self, pnt, d=.0):
        """Permet de savoir si le joueur est du bon cote de la face"""
        if d < 0:
            raise MustBePositive

        # return self.v_normal.produit_scal(Vecteur(self.base.origine, player.pos)) = 0
        return - d <= self.v_normal[0] * (pnt[0] - self.origine[0]) \
                    + self.v_normal[1] * (pnt[1] - self.origine[1]) \
                    + self.v_normal[2] * (pnt[2] - self.origine[2]) <= d
