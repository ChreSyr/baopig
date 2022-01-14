import math
import pygame


def modif_HSV(image, dh, ds, dv):
    """
    Renvoi une copie de l'image avec des couleurs modifiees

    :param image: L'image a modifier
    :param dh: On ajoute dh a la Hue (teinte) - modulo 360
    :param ds: On ajoute ds a la Saturation (intensite) - entre 0 et 255
    :param dv: On ajoute dv a la Value (brillance) - entre 0 et 255
    :return: L'image modifiee selon les parametres
    """
    # x, y = image.get_size()
    x = image.get_width()
    y = image.get_height()
    new_image = pygame.Surface((x, y)).convert_alpha()
    new_image.fill((255, 255, 255, 0))

    for i in range(x):
        for j in range(y):
            # On commence par convertir en tsv
            (r, g, b, a) = image.get_at((i, j))
            (h, s, v) = rgb_to_hsv(r, g, b)

            # On fait les modif qu'on veut
            h = modulo(h + dh, 360)
            s = s + ds if s + ds < 255 else 255
            v = v + dv if v + dv < 255 else 255

            # Ensuite on repasse en rgb
            (r, g, b) = hsv_to_rgb(h, s, v)

            new_image.set_at((i, j), (r, g, b, a))
    return new_image

def resize(image, size):
    """
    Renvoi une copie de l'image redimensionnee aux dimensions "size"

    :param image: L'image a modifier
    :param size: Les nouvelles dimensions
    :return: L'image redimensionnee
    """
    new_image = pygame.Surface(size).convert_alpha()
    # NOTE : Utile ?
    new_image.fill((255, 255, 255, 0))

    w, h = size
    coef_x = image.get_width()/w
    coef_y = image.get_height()/h

    for i in range(w):
        for j in range(h):
            new_image.set_at((i, j), image.get_at((int(i*coef_x), int(j*coef_y))))
    return new_image

def rotate(image, angle):
    """
    Renvoi une copie de l'image tournee selon l'angle dans le sens trigonometrique
    NOTE : Pas au point
            La rotation est decalee par rapport au centre

    :param image: L'image a modifier
    :param angle: L'angle de rotation, en radian
    :return: L'image orientee selon l'angle
    """

    def get_proj(pnt, angle):
        """
        Renvoi la position du vecteur (0, 0) -> point tournee selon l'angle dans le sens trigonometrique

        :param pnt: Le point a modifier
        :param angle: L'angle de rotation, en radian
        :return: Le point tourne selon l'angle
        """
        return round(pnt[0] * math.cos(angle) - pnt[1] * math.sin(angle)), \
               round(pnt[0] * math.sin(angle) + pnt[1] * math.cos(angle))

    x = image.get_width()
    y = image.get_height()
    new_image = pygame.Surface((x, y)).convert_alpha()
    new_image.fill((255, 255, 255, 0))
    o = (x / 2, y / 2)
    o2 = get_proj(o, angle)
    (ox, oy) = (o[0] - o2[0], o[1] - o2[1])
    d = math.sqrt(2)
    for i in range(math.floor(-x*d), math.ceil(x*d)):
        for j in range(math.floor(-y*d), math.ceil(y*d)):
            (x2, y2) = get_proj((i, j), angle)
            if 0 <= x2 < x and 0 <= y2 < y:
                color = image.get_at((x2, y2))
                new_image.set_at((round(i+oy), round(j+ox)), color)

    return new_image

def sub_alpha(img, alpha):
    """
    Applique une transparence sur l'image

    :param img: L'image a modifier
    :param alpha: La valeur de la transparence - entre 0 et 255
    """
    voile = pygame.Surface(img.get_rect().size, pygame.SRCALPHA)
    voile.fill((0, 0, 0, alpha))
    img.blit(voile, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

def rgb_to_hsv(r, g, b):
    """
    Renvoi un pixel de format RGB en format HSV

    :param r: La valeur Red du pixel
    :param g: La valeur Green du pixel
    :param b: La valeur Blue du pixel
    :return: Le pixel en format HSV
    """
    ma = max(r, g, b)
    mi = min(r, g, b)
    if ma == mi:
        h = 0
    elif ma == r:
        h = modulo(60 * (g - b) / (ma - mi), 360)
    elif ma == g:
        h = 60 * (b - r) / (ma - mi) + 120
    else:
        h = 60 * (r - g) / (ma - mi) + 240
    if ma == 0:
        s = 0
    else:
        s = 1 - mi / ma
    v = ma

    return h, s, v

def hsv_to_rgb(h, s, v):
    """
    Renvoi un pixel de format HSV en format RGB

    :param h: La valeur Hue du pixel
    :param s: La valeur Saturation du pixel
    :param v: La valeur Value du pixel
    :return: Le pixel en format RGB
    """
    hi = int(h/60) % 6    # = int(h/60) modulo 6
    f = h/60 - hi
    l = v * (1 - s)
    m = v * (1 - f * s)
    n = v * (1 - (1 - f) * s)

    if hi == 0:
        return v, n, l
    elif hi == 1:
        return m, v, l
    elif hi == 2:
        return l, v, n
    elif hi == 3:
        return l, m, v
    elif hi == 4:
        return n, l, v
    else:
        return v, l, m

