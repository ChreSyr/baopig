
import math
from biblios.BiblioEspacesVect import Polygon3


class Functions:

    @staticmethod
    def cut_pol(plan, pol):
        """Renvoi la partie du polygone qui est devant le plan"""

        # On regarde tous les segments
        pnt_is_facing = [plan.facing(pnt) for pnt in pol]

        # Si le polygone est entierement devant le plan
        if False not in pnt_is_facing:
            return pol
        # Si le polygone est entierement derriere le plan
        elif True not in pnt_is_facing:
            return None

        # Methode qui obtient la partie du pol qui est devant le plan
        cut_pol = Polygon3()
        last_pnt_is_facing = pnt_is_facing[0]
        for i, pnt in enumerate(pol):
            this_pnt_is_facing = pnt_is_facing[i]
            if this_pnt_is_facing != last_pnt_is_facing:
                cut_pol.append(plan.intersection(pnt, pol[i - 1]))
            if this_pnt_is_facing:
                cut_pol.append(pnt)
            last_pnt_is_facing = this_pnt_is_facing
        if last_pnt_is_facing != pnt_is_facing[0]:
            cut_pol.append(plan.intersection(pol[0], pol[-1]))

        return cut_pol

    @staticmethod
    def distance(pnt1, pnt2):
        return math.sqrt((pnt2[0] - pnt1[0]) ** 2 + (pnt2[1] - pnt1[1]) ** 2 + (pnt2[2] - pnt1[2]) ** 2)


fc = Functions()
