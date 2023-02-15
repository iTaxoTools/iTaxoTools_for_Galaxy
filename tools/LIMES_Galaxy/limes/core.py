## -*- coding:Latin-1 -*-

"""
Définit les classes et fonctions suivantes :

    Espace()
    Printer()

Les méthodes de Esapce permettent de calculer les différents indices Ttax, Ctax,
Mtax. Les fonctions de base pour calculer ces indices sont union() et
intersection(). La fonction communes() sert à calculer les partitions (voir
module "partition").

Printer() produit la représentation formatée qui peut être affichée dans
l'interface (voir wlimes) ou produite dans un fichier ou à l'écran.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from operator import attrgetter,itemgetter
import weakref,re

from typing import (Optional,Union,Mapping,cast,List,overload,TYPE_CHECKING,
                    DefaultDict,Iterator,Tuple,Sequence,Collection,Dict)

ALGO_CTAX=0
ALGO_MRATIO=1

# -- Messages multilingues ------------

_langue=0

"""
Rend la langue courante, éventuellement après l'avoir affectée à 'lg si !=None.
"""
def set_langue(lg: Optional[int] =None) -> int:
    global _langue
    if lg is not None:
        _langue=lg
    return _langue

MLMsgType=Sequence[str]

"""
Les arguments donnent les messages équivalents dans les différentes langues
supportées. Dans la version actuelle : français, anglais.
Rend le message (élément de 'msgs) correspondant à la langue courante.
"""
def get_text(*msgs:str) -> str:
    return msgs[_langue]

# -- Utilitaires ------------

class RedundantNameError(ValueError):
    pass

class EmptyMethodError(ValueError):
    pass

CodeEspeceType=Union[int,str]

# -- Méthodes ------------

NOM=attrgetter("nom")

"""
Echantillon(nom)

Représente un échantillon = specimen.

L'instance est hashable, et l'égalité avec les autres instances de Echantillon
repose sur .nom.

Attributs :
    .nom    Nom fourni à la création.
"""
class Echantillon:
    def __init__(self,nom: str):
        self.nom=nom

    def __repr__(self):
        return "%s(%s)"%(self.__class__.__name__,self.nom)

    def __str__(self):
        return self.nom

    # Les méthodes __hash__() et __eq__() sont utiles pour mettre les
    # Echantillon dans des set (monofmt, test_limes) ou des dict.
    #
    def __hash__(self):
        return hash(self.nom)

    def __eq__(self,other):
        if isinstance(other,Echantillon):
            return self.nom==other.nom
        return NotImplemented

"""
Methode(nom,echantillons,codesespeces,source=None)

'echantillons et 'codesespeces sont les listes des Echantillon et du code
espèce associé à chacun, extrait d'une colonne du tableau source, dans l'ordre
de ce tableau. Les éléments de 'codesespeces sont de type quelconque (int,
str). Les Methode sont créées par les readers. 'source est l'instance de Source
à laquelle appartient la méthode.

L'instance est le dictionnaire donnant pour chaque Echantillon son code espèce.

L'instance dispose des attributs et méthodes suivants :
    .nom        Nom fourni à la création.
    .especes    Liste des espèces : il s'agit d'un dictionnaire (non ordonné) :
                la clef est le code d'espèce, la valeur le set des Echantillon.
                len(self.especes) est donc le nombre d'espèces identifiées par
                la méthode.
    .source     L'instance de Source à laquelle appartient la Methode.
"""
class Methode(dict):

    especes: EspeceType

    def __init__(self,nom: str,
                 echantillons: Sequence[Echantillon],
                 codesespeces: Sequence[CodeEspeceType],
                 source: Optional[Source] =None):
        super().__init__(zip(echantillons,codesespeces))
        self.nom=nom
        if source: self.source=weakref.proxy(source)
        # On pourrait ajouter le test que le nombre d'échantillons est >=1.
        # Pour le moment, ceci est inutile car le test a toujours été réalisé
        # en amont par les reader.

    def __setitem__(self,*args,**kw):
        raise TypeError("Read only object")
    clear=__delitem__=pop=popitem=setdefault=update=__setitem__ # type: ignore

    def __str__(self):
        return self.nom

    def __repr__(self):
        return self.nom+"("+", ".join(e.nom for e in self)+")"

    def __getattr__(self,attr: str):
        if attr=="especes":
            dd: DefaultDict[CodeEspeceType,set] =defaultdict(set)
            for ech,esp in self.items():
                dd[esp].add(ech)
            self.especes=dict((e,frozenset(s)) for e,s in dd.items())
            return self.especes
        raise AttributeError(attr)

##    @property
##    def especes(self) -> EspeceType:
##        if not hasattr(self,"_especes"):
##            dd: DefaultDict[CodeEspeceType,set] =defaultdict(set)
##            for ech,esp in self.items():
##                dd[esp].add(ech)
####            for esp in dd:
####                dd[esp]=cast(set,frozenset(dd[esp]))
##            self._especes=dict((e,frozenset(s)) for e,s in dd.items())
##        return self._especes

class pEchantillon(Echantillon):
    pass
    # Le pEchantillon doit être hashable, et la comparaison basée sur le nom,
    # pour la comparaison avec un RefEchantillon dans test_limes (par ex. :
    # test_partitions.exec_test()).
    # La hashabilité est héritée de Echantillon.

    # Dans un Espace, il y a toujours 1 seul pEchantillon portant un nom
    # donné. Les pEchantillon peuvent dont toujours être comparés par
    # l'identité. Dès lors, il n'ont pas besoin de __eq__() ni de __hash__() :
    # les fonctions de object suffisent, et sont plus efficaces. Cependant,
    # ces fonctions sont héritées de Echantillon -> peut-être n'y a-t-il pas
    # d'utilité à ce que pEchantillon dérive de Echantillon.

PaquetType=Collection[Echantillon]
EspeceType=Mapping[CodeEspeceType,PaquetType]
PaquetListeType=Collection[PaquetType]

"""
pMethode(meth,mdict,an)

Une pMethode représente une Methode dans un Espace. Elle est équivalente à
la Methode d'origine, mais les échantillons sont représentés par des
pEchantillon au lieu des Echantillon ; les pEchantillon ont été normalisés
entre les différentes méthodes de l'Espace.

La pMethode peut comprendre :
    - moins d'échantillons que l'Espace dans lequel elle a été créée, si
        d'autres méthodes contiennent des échantillons absent de 'meth.
    - moins d'échantillons que 'meth, si l'Espace a été créé avec l'option
        common=True, et que les échantillons non communs ont été exclus.

'meth est la Methode d'origine. 'mdict est un dictionnaire {nom: pEchantillon},
donnant l'ensemble des pEchantillon créés dans l'espace ; 'nom est le nom du
pEchantillon. 'an est un dictionnaire {old: new} donnant le nom 'new du
pEchantillon correspondant au nom 'old dans la Methode d'origine. 'old et 'new
peuvent être différents si les noms des échantillons ont été normalisés.

Noter que 'mdict peut contenir des échantillons absents de la Methode (échan-
tillons présents dans d'autres méthodes de l'espace), et inversemment (échan-
tillons non communs à toutes les méthodes de l'espace). La pMethode créée ne
contiendra que les échantillons communs aux deux.

L'instance est le dictionnaire des pEchantillon. Elle est hashable, et
l'égalité avec les autres instances de pMethode repose sur .nom.

L'instance dispose des attributs et méthodes suivants :
    .nom        Egal au nom 'eff_nom passé à la création si !=None, ou au nom
                de la Methode 'meth sinon.
    .meth       La Methode 'meth fournie à la création.
    .especes    Comme meth.especes, mais les éléments sont des set de
                pEchantillon et non d'Echantillon.
    .all        Dictionnaire pE -> E, donnant l'Echantillon 'E dans 'meth
                correspondant au pEchantillon 'pE composant l'instance. Pour
                les pEchantillon absents de la pMethode, 'E vaut None. .all
                contient tous les échantillons de l'Espace dans lequel
                l'instance a été créée.
    .exclus     Liste des Echantillon de 'meth non repris dans la pMethode,
                ou None s'il n'y en a pas. Des échantillons ont pu être exclus
                si l'Espace a été créé avec l'option common=True.
    .ctax()

Elle hérite également de tous les attributs de la Methode 'meth, et notamment :
    .source     L'instance de Source.
"""
class pMethode(Methode):
    def __init__(self,meth: Methode,mdict: Dict[str,pEchantillon],
                 an: Dict[str,str],eff_nom: Optional[str] =None):
        mdict=mdict.copy()
        loc=[]
        codesp=[]
        all={}
        exclus=[]
        for ech,esp in meth.items():
            new=an[ech.nom] # hors try: car doit tj être présent.
            try:
                pe=mdict.pop(new)
            except KeyError:
                exclus.append(ech)
                # Echantillon exclus, non commun à toutes les Methode.
            else:
                loc.append(pe)
                codesp.append(esp)
                all[pe]=ech
        for pe in mdict.values():
            all[pe]=None
        super().__init__(eff_nom or meth.nom,loc,codesp)
        self.meth=meth
        self.all=all
        self.exclus=exclus or None
        self.__ctax: dict[pMethode,tuple[PaquetListeType,PaquetListeType]] ={}
        # Le dictionnaire est calculé au premier appel, puis stocké.

    def __getattr__(self,attr):
        return getattr(self.meth,attr)

    # Les fonctions __eq__(), __ne__() et __hash__() sont nécessaires pour
    # l'utilisation dasn un dict, par exemple dans .__ctax. La comparaison est
    # basée sur le nom.
    #
    def __eq__(self,other):
        if isinstance(other,pMethode):
            return self.nom==other.nom
        return NotImplemented

    __ne__=object.__ne__
    # Pour masquer dict.__ne__().

    def __hash__(self):
        return hash(self.nom)

    @overload
    def ctax(self,m2: pMethode,force: bool) \
                    -> Optional[tuple[PaquetListeType,PaquetListeType]]: ...

    @overload
    def ctax(self,m2: pMethode) \
                    -> tuple[PaquetListeType,PaquetListeType]: ...

    # Calcule l'intersection et l'union des événements de spéciation entre les
    # deux pMethode 'self et 'm2. Rend le couple (a,b) où 'a est la liste des
    # groupes de pEchantillon de l'intersection et 'b la liste des groupes
    # de pEchantillon de l'union.
    # Les listes ne sont calculées qu'au premier appel et conservées pour les
    # appels suivant.
    # Si les listes n'ont pas encore été calculées, le calcul est réalisé si
    # 'force vaut True. Si 'force vaut False, le calcul n'est pas réalisé et la
    # fonction rend None.
    # Ainsi, dans tous les cas, rend une valeur vraie (le couple) si
    # l'intersection est disponible, fausse (None) sinon.
    #
    def ctax(self,m2: pMethode,force: bool =True) \
                    -> Optional[tuple[PaquetListeType,PaquetListeType]]:
        if m2 not in self.__ctax:
            if force:
                self.__ctax[m2]=(intersection(self,m2),union(self,m2))
            else:
                return None
        return self.__ctax[m2]

# -- Calculs union / intersection ------------

def _meths_arg(meths):
    if len(meths)==1:
        m=meths[0]
        if not isinstance(m,pMethode): meths=m
    return meths

"""
Rend la liste des paquets, c-à-d des groupes (set) de pEchantillon communs à
toutes les pMethode de la liste 'meths. On peut soit fournir les pMethode en
arguments, soit fournir comme unique argument la liste des pMethode.

Pour constituer les paquets :
    - On part d'un paquet constitué de tous les échantillons.
    - Pour la première méthode, on scinde ce paquets en autant d'espèces,
        chacun regroupant les échantillons d'une espèce.
    - Pour la 2ième méthode, on reprend chacun des paquets, et on le scinde
        en autant de paquets qu'il faut pour que aucun ne contienne des
        échantillons d'espèces différentes de cette méthode.
    - Pour la 3ième méthode, on reprend chacun des paquets que l'on scinde à
        nouveau, et ainsi de suite.
"""
def union(*ameths: Union[pMethode,list[pMethode],Espace]) -> PaquetListeType:
    meths: list[pMethode] = _meths_arg(ameths)

    """
    Pour chaque paquet de la liste 'paqs, analyse s'il doit être scindé
    à partir de la constitution de la pMethode 'meth. Rend une nouvelle
    liste de paquets, constituée à partir de la première, mais où certains
    paquets ont pu être scindés en plusieurs.
    """
    def splitpaqs(meth: pMethode,paqs: PaquetListeType)-> PaquetListeType:
        paqs2: List[PaquetType] =[]
        for paq in paqs:
            ll=defaultdict(set)
            for e in paq:
                ll[meth[e]].add(e)
                # 'll est un dict donnant, pour chaque espèce à laquelle
                # appartient au moins 1 échantillon du paquet traité 'paq,
                # le set des échantillons appartenant à cette espèce. Il
                # faudra donc scinder le paquet en autant de paquets qu'il
                # y a d'espèces.
            paqs2.extend(ll.values())
            # Chaque valeur de 'll représente un set d'échantillons
            # appartenant à une espèce distincte selon la méthode 'meth.
            # Ce set doit donc constituer un paquet distinct. Noter
            # qu'il se peut que tous les échantillons appartiennent à la
            # même espèce, auquel cas l'unique nouveau paquet
            # ll.values()[0] est identique au paquet d'origine 'paq.
        return paqs2

    paqs: PaquetListeType =[set(meths[0])]
        # 'paqs est la liste des paquets. On part d'une liste avec un seul
        # paquet, comprenant tous les échantillons (liste de la première
        # méthode ; toutes les méthodes sont supposées avoir la même liste
        # d'échantillons, par construction).
    for m in meths:
        paqs=splitpaqs(m,paqs)
            # Pour chaque Methode, splitpaqs() traite la liste courante de
            # paquets et rend une nouvelle liste, constituée à partir de la
            # première mais où certains paquets ont pu être scindés en
            # plusieurs. La liste rendue constitue la liste en entrée pour
            # le cycle suivant.
    return paqs

"""
Rend la liste des paquets (set) correspondant à l'intersection des événements
de spéciation des pMethode de la liste 'meths. On peut soit fournir les
pMethode en arguments, soit fournir comme unique argument la liste des
pMethode.

Pour créer un paquet :
    - On prend un échantillon non encore pris dans un paquet, et on le met dans
        le nouveau paquet.
    - On recherche dans chacune des méthodes l'espèce qui inclut cet
        échantillon.
    - On ajoute dans le paquet tous les échantillons constituant cette espèces.
    - Quand on a parcouru toutes les méthodes, on recommence en considérant
        chacun des échantillons qu'on a ajouté au cycle précédent, qui peuvent
        ainsi attirer d'autres espèces.
    - On a fini le paquet quand le parcours des méthodes n'ajoute plus de
        nouvel échantillon.
"""
def intersection(*ameths: Union[pMethode,list[pMethode]]) -> PaquetListeType:
    meths: list[pMethode] = _meths_arg(ameths)
    pool=set(meths[0]) # pool = ensemble de tous les échantillons
    inter: List[PaquetType] =[]
    while pool:
        paq=set()
        paq.add(pool.pop())
        # On prend un échantillon restant, on le place dans 'paq, puis on va
        # chercher la fermeture transitive à partir de celui-ci.
        nb=0
        while nb!=len(paq):
            # On reboucle sur les méthode tant que le traitement a ajouté un
            # échantillon -> fermeture transitive.
            nb=len(paq)
            for m in meths:
                for e in list(paq): # list() car le 'paq est modifié ensuite.
                    # Remarque : on reprend ici tous les échantillons dans le
                    # paquet. En théorie, on pourrait optimiser en ne considé-
                    # rant que les échantillons ajoutés au cycle while
                    # précédent. Noter cependant que chaque méthode "profite"
                    # des échantillons ajoutés dans le même cycle while pour
                    # les méthodes précédentes.
                    for p in m.especes.values():
                        if e in p:
                            paq.update(p)
                            break
                            # break parce qu'un échantillon ne peut se trouver
                            # que dans une espèce et une seule.
        inter.append(paq)
        pool.difference_update(paq)
    return inter

"""
Rend la liste des espèces communes à toutes les pMethode de la liste 'meths,
c-à-d les espèces constituées des mêmes pEchantillon. Les espèces rendues sont
constituées du set des pEchantillon. La liste rendue n'est pas ordonnée, mais
est consistante (l'ordre sera toujours le même avec la même liste de méthodes).
"""
def communes(meths: List[pMethode]) -> PaquetListeType:
    comm: List[PaquetType] =[]
    if meths:
        m0=meths[0]
        meths=meths[1:]
        for p in m0.especes.values():
            ok=True
            for m in meths:
                if p not in m.especes.values():
                    ok=False
                    break
            if ok:
                comm.append(p)
    return comm

# -- Espace de travail ------------

IndiceType=Tuple[int,int,Optional[float]]

"""
Espace(meths,strict=True,common=False)

Crée l'espace combinant toutes les Methode de la liste 'meths. Chaque Methode
est représentée par une pMethode. Le Espace est le tuple de ces pMethode,
dans le même ordre que 'meths.

Dans les pMethode, les Echantillon sont remplacés par des pEchantillon. Toutes
les pMethode du Espace partagent le même jeu de pEchantillon ; l'égalité est
donc assimilable à l'identité ("is" peut être utilisé à la place de ==, ce qui
est plus efficace).

Si 'strict vaut True, les Echantillon sont identifiés entre les Methode par
leur nom exact. Si 'strict vaut False, les noms des Echantillon sont norma-
lisés : la casse est forcée en minuscule, et toutes les séquences de caractères
spéciaux sont remplacées par un '_'. C'est sous ce nom normalisé que sont
faites les correspondances entre les Methode, et ce sera aussi le nom des
pEchantillon. Génère une exception RedundantNameError si deux échantillons
d'une même Methode portent le même nom après normalisation.

Si 'common vaut False, les pMethode comporteront la même liste d'échantillons
que la Methode d'origine. Si 'common vaut True, seuls sont pris en compte les
échantillons communs à toutes les Methode. Les pMethode ne comporteront alors
que ces échantillons communs ; leur attribut .exclus donne la liste des
échantillons ainsi exclus. L'attribut .meth_modif comptabilise les méthodes
dont on a ainsi exclus des échantillons. Une exception EmptyMethodError est
générée s'il n'y a aucun échantillon commun.

L'instance dispose des attributs et méthodes suivants :
    .echantillons   La liste des pEchantillon. Ils sont tous référencés par
                    au moins une pMethode. Si 'common vaut True, il ne s'agit
                    que des échantillons communs, qui sont alors tous
                    référencés par toutes les pMethode.
    .nbech          Nombre d'échantillons.
    .meth_modif     Nombre de méthodes dont certains échantillons ont été
                    exclus par l'option 'common (forcément 0 si 'common vaut
                    False).
    .exclus         Nombre d'échantillons exclus si common=True (0 si False).
    .paquets        Liste des paquets, c-à-d des groupes (set) de pEchantillon
                    communs à toutes les pMethode.
    .sorted()
    .rtax()
    .irtax()
    .ctax()
    .ictax()
    .mctax()
    .match_ratio()
    .imatch_ratio()
    .communes()
"""
class Espace(tuple):
    rex=re.compile(r"\W+",re.ASCII)

    echantillons: List[pEchantillon]
    meth_modif: int
    exclus: int

    """
    Le fonction de normalisation des noms d'échantillon si 'strict==False.
    """
    @staticmethod
    def normalise(nom):
        return Espace.rex.sub("_",nom.lower())

    def __new__(cls,meths: list[Methode],strict: bool=True,common: bool=False) \
                                                                    -> Espace:
        echs: DefaultDict[str,int] =defaultdict(int)
        # nouveau nom -> nombre de Methode contenant cet échantillon
        andict: dict[str,str]={}
        # ancien nm -> nouveau nom d'échantillon
        cptmeth: DefaultDict[str,int] =defaultdict(int)
        # nom de méthode -> nombre de méthodes portant ce nom
        for m in meths:
            cptmeth[m.nom]+=1
            mechs=set()
            for e in m:
                old=e.nom
                new=old if strict else Espace.normalise(old)
                if new in mechs:
                    raise RedundantNameError(
                        get_text("Méthode %s: échantillons %s redondant "
                                 "après normalisation",
                                 "Method %s: sample %d redondant after "
                                 "normalisation")%(m.nom,old))
                andict[old]=new
                mechs.add(new)
                echs[new]+=1
        nbmeths=len(meths)
        dictechs=dict((n,pEchantillon(n)) for n in sorted(echs)
                      if not common or echs[n]==nbmeths)
        # nouveau nom -> pEchantillon portant ce nom
        # tous, ou seulement les communs si 'common==True
        if not dictechs:
            raise EmptyMethodError(
                get_text("Pas d'échantillons communs entre toutes les méthodes",
                         "No common samples between all methods"))

        # Renommage des noms de méthodes.
        redond=set(nom for nom,nb in cptmeth.items() if nb>1)
        names=set(m.nom for m in meths if m.nom not in redond)
        cptredond=dict((nom,0) for nom in redond)
        lstpm: List[pMethode]=[]
        for m in meths:
            nom=m.nom
            if nom in redond:
                while True:
                    cptredond[nom]+=1
                    new=nom+"_"+str(cptredond[nom])
                    if new not in names:
                        names.add(new)
                        pm=pMethode(m,dictechs,andict,eff_nom=new)
                        break
            else:
                pm=pMethode(m,dictechs,andict)
            lstpm.append(pm)

        me=super().__new__(cls,cast(list,lstpm)) # cast nécessaire ?
        me.echantillons=list(dictechs.values())
        me.meth_modif=len([m for m in me if m.exclus])
        me.exclus=len(echs)-len(dictechs)
        return me

    @property
    def paquets(self) -> PaquetListeType:
        if not hasattr(self,"_paqs"):
            self._paqs=union(self)
        return self._paqs

    @property
    def nbech(self) -> int:
        return len(self.echantillons)

    """
    Rend le Rtax de la méthode 'meth, sous la forme d'un triplet (a,b,c)
    comme suit :
        a = numérateur (int) = nb. d'événements de spéciation identifiés par la
            méthode.
        b = dénominateur (int) = nb. d'événements de spéciations pour toutes
            les méthodes de l'espace (union).
        c = a/b (float) ; None si 'b vaut 0.
    """
    def rtax(self,meth: pMethode) -> IndiceType:
        n=len(meth.especes)-1
        d=len(self.paquets)-1
        return (n,d,(n/d if d else None))

    """
    Rend un itérateur donnant la liste des pMethode de l'espace triées par leur
    nom .nom.
    """
    def sorted(self) -> Iterator[pMethode]:
        yield from sorted(self,key=NOM)
            
    """
    Rend un itérateur retournant le Rtax pour toutes les méthodes de l'espace,
    sous la forme de couples (m,(a,b,c)), où 'm est la pMethode et (a,b,c) le
    Rtax de cette méthode exprimé comme dans .rtax(). Les éléments retournés
    sont triés par ordre alphabétique des noms de méthodes.
    """
    def irtax(self) -> Iterator[tuple[pMethode,IndiceType]]:
        for m in self.sorted():
            yield (m,self.rtax(m))

    """
    Rend le Ctax associé au couple de méthodes 'meth1 / 'meth2, sous la forme
    d'un triplet (a,b,c) comme suit :
        a = numérateur (int) = nb. d'événements de spéciation communs aux
            deux méthodes (intersection).
        b = dénominateur (int) = nb. d'événements de spéciations identifiés
            par l'une ou l'autre méthode (union).
        c = a/b (float), ou None si 'b vaut 0.
    """
    @staticmethod
    def ctax(meth1: pMethode,meth2: pMethode) -> IndiceType:
        i,u=meth1.ctax(meth2,False) or meth2.ctax(meth1,False) or \
                                                             meth1.ctax(meth2)
        # On regarde d'abord si le calcul a déjà été fait sur 'meth1 puis
        # 'meth2 ; si non, on force le calcul sur 'meth1.
        ni=len(i)-1
        nu=len(u)-1
        f=ni/nu if nu else None
        return (ni,nu,f)

    """
    Rend un itérateur retournant le Ctax pour tous les couples de méthodes de
    l'espace, sous la forme de triplet (m1,m2,(a,b,c)), où 'm1 et 'm2 sont les
    méthodes et (a,b,c) le Ctax de ce couple exprimé comme dans .ctax(). Les
    éléments retournés sont triés par ordre alphabétique de 'm1 puis de 'm2.
    """
    def ictax(self) -> Iterator[tuple[pMethode,pMethode,IndiceType]]:
        for m1,m2 in combinations(self.sorted(),2):
            yield (m1,m2,self.ctax(m1,m2))

    """
    Calcule la moyenne des ctax entre la méthode 'meth est les autres méthodes
    de l'espace. Rend cette moyenne sous forme de float, ou None si la moyenne
    n'a pas de sens (pas d'autres méthodes avec laquelle le Ctax avec 'meth a
    un sens).
    """
    def mctax(self,meth: pMethode) -> Optional[float]:
        nb=0
        sum=0.0
        for meth2 in self:
            if meth!=meth2:
                _,_,c=self.ctax(meth,meth2)
                if c is not None:
                    nb+=1
                    sum+=c
        return sum/nb if nb else None

    """
    Rend le match ratio associé au couple de méthodes 'meth1 / 'meth2, sous la
    forme d'un triplet (a,b,c) comme suit :
        a = numérateur (int) = nb. d'espèces identiques entre les deux méthodes.
        b = dénominateur (int) = somme des nb. d'espèces des deux méthodes.
        c = a/b (float)
    """
    @staticmethod
    def match_ratio(meth1: pMethode,meth2: pMethode) -> IndiceType:
        e1=set(meth1.especes.values())
        e2=set(meth2.especes.values())
        a=len(e1&e2)*2
        b=len(e1)+len(e2)
        return (a,b,a/b)

    """
    Rend un itérateur retournant le match ratio pour tous les couples de
    méthodes de l'espace, sous la forme de triplet (m1,m2,(a,b,c)), où 'm1 et
    'm2 sont les noms des méthodes et (a,b,c) le match ratio de ce couple
    exprimé comme dans .match_ratio(). Les éléments retournés sont triés par
    ordre alphabétique de 'm1 puis de 'm2.
    """
    def imatch_ratio(self) -> Iterator[tuple[pMethode,pMethode,IndiceType]]:
        for m1,m2 in combinations(self.sorted(),2):
            yield (m1,m2,self.match_ratio(m1,m2))

    """
    Rend la liste des espèces communes à toutes les Methode dont la liste est
    passée en argument, c-à-d les espèces constituées des mêmes échantillons.
    Les espèces rendues sont constituées du tuple ordonné des Echantillon. La
    liste rendue n'est pas ordonnée, mais est consistante (l'ordre sera
    toujours le même avec la même liste de méthodes).
    """
    communes=staticmethod(communes)

"""
Printer(espace)

Le Printer facilite l'affichage des coefficients. 'espace est le Espace à
afficher. L'utilisateur peut subclasser Printer et redéfinir les méthodes
.print() et .index().

Le Printer dispose des attributs et méthodes suivants :
    .avec_alias Si True, les noms des méthodes sont trop longs et seront
                substitués par des codes dans les en-têtes de lignes et de
                colonnes. Si False, les noms de méthodes sont courts et ne
                seront pas substitués.
    .codes      Itérable donnant la liste des libellés affichés, dans l'ordre
                de 'espace. Il s'agit d'une liste de codes de substitution si
                .avec_alias vaut True, des noms .nom des méthodes sinon.
    .espace     L'argument 'espace passé à la création.
    .pralias()
    .prtable()
    .nl()

La classe peut être dérivée pour afficher ailleurs qu'à l'écran. La classe
dérivée peut redéfinir les méthodes suivantes :
    .print()
    .index()
"""
class Printer:
    MAXMNAME=6  # nb. max de caractères d'une méthode.
    NBDEC=2     # nb. de décimales des rapports.

    def __init__(self,espace: Espace):
        self.espace=espace
        self.codes=[NOM(m) for m in espace]
        ln=max(map(len,self.codes))
        self.avec_alias=ln>self.MAXMNAME
        if self.avec_alias:
            nb=len(espace)
            fmt="M%%0%dd"%(1 if nb<10 else (2 if nb<100 else 3))
            self.codes=[fmt%m for m,a in enumerate(self.codes,start=1)]
        # Si un nom de méthode dépasse MAXMNAME caractères, on crée des codes
        # artificiels ; .avec_alias vaut alors True (False sinon).
        # .codes donne la liste des noms de méthodes à afficher, dans le même
        # ordre que l'Espace. Si .avec_alias vaut False, ce sont les noms
        # (.nom) des Methode. Si .avec_alias vaut True, ce sont des codes
        # générés artificiellement.

        sz0=max(map(len,self.codes))
                # Colonne 0 : longueur max d'un code ou nom de méthode.
        szA1=len("%d"%max(map(len,map(attrgetter("especes"),espace))))
                # Long. max du nombre d'échantillons dans une espèce.
        szA2=7  # Longueur max d'un rapport A/B. On suppose qu'il y aura au
                # plus 999 échantillons -> 3+3+1 car.
        szA3=szA2
        szB1=self.NBDEC+2
                # Long. d'un flottant < 1, avec NBDEC décimales.
        szB2=szB1
        szB3=szB1
        sz1=max(szA1,szB1,5)
                # La colonne 1 contient les nb. d'échantillons par espèce
                # (szA1), des flottant<1 (avec NBDEC décimales) (szB1), et le
                # mot "mCtax".
        sz2=max(szA2,szB2,4)
                # La colonne 2 contient des rapports (szA2), des flottants<1
                # (szB2), et le mot "Rtax".
        sz3=max(szA3,szB3,4,sz0)
                # Les colonnes 3 contiennent des rapports (szA3), des flottants
                # (szB3), le mot "Ctax", et les codes/noms des méthodes (sz0).
        bl0=4 # Blancs séparateurs avec la colonne suivante.
        bl1=2
        bl2=2
        bl3=2
        self.__sizes=((sz0,bl0),(sz1,bl1),(sz2,bl2),(sz3,bl3))
        # Chaque élement correspond à une colonne : colonne 0 (noms des
        # méthodes), colonne 1 (Esp/mCtax), colonne 2 (Rtax), colonnes 3
        # (colonnes des Ctax, table proprement dite).
        # Chaque élement est un couple (a,b), où 'a est la largeur de la
        # colonne, et 'b le nombre de blancs qui la séparent de la colonne
        # suivante.

    """
    Affiche 'a sur une zone de 'sz caractères, cadré à droite, suivi de 'bl
    blancs. 'a a l'un des format suivant :
        - str : chaîne
        - int : entier
        - float : x.00
        - (n,d) : rapport n/d
        - None : "N/A"
    """
    def __pr(self,a:Union[str,int,float,tuple[int,int],None],sz: int,
             bl: int =0):
        if isinstance(a,tuple):
            if a[1]==0:
                a="N/A"
            else:
                a="%d/%d"%a
        elif isinstance(a,float): a="{:.{}f}".format(a,self.NBDEC)
        elif a is None: a="N/A"
        # else 'a est un str, qu'on prend tel quel.
        self.print("{:>{}}{}".format(a,sz," "*bl))

    """
    Si les méthodes ont dû être renommées, affiche la table de correspondance
    et rend True. Sinon, ne fait rien et rend False.
    """
    def pralias(self) -> bool:
        if self.avec_alias:
            ln=max(map(len,self.codes))
            for code,m in zip(self.codes,self.espace):
                self.print("{:{}} = {}\n".format(code,ln,NOM(m)))
        return self.avec_alias

    # 'algo_ctax vaut True pour le calcul des Ctax, False pour le calcul du
    # match ratio.
    #
    def __prcommon(self,fractions: bool,algo_ctax: bool):
        get_rapp=itemgetter(0,1) if fractions else itemgetter(2)
        sizes=self.__sizes
        espace=self.espace

        self.index(0)
        self.__pr("",*sizes[0])
        self.__pr("Esp" if fractions or not algo_ctax else "mCtax",*sizes[1])
        self.__pr("Rtax" if algo_ctax else "",*sizes[2])
        s=" "*(sizes[3][0]-len(next(iter(self.codes)))) + \
                   ("Ctax" if algo_ctax else "Match Ratio") + \
                   " -->"
        self.print(s)
        self.print(" "*(sum(sizes[3])*len(espace)-len(s)))
        self.index(1)
        self.nl()

        self.index(2)
        self.__pr("",sum(a+b for a,b in sizes[:3]))
        for i,m in enumerate(self.codes):
            self.index(10,i)
            self.__pr(m,*sizes[3])
            self.index(11,i)
        self.index(3)
        self.nl()

        fn=espace.ctax if algo_ctax else espace.match_ratio
        for i,(cd,meth) in enumerate(zip(self.codes,espace)):
            self.index(4,i)
            self.print("{:<{}}{}".format(cd,sizes[0][0]," "*sizes[0][1]))
            self.index(5)
            if fractions or not algo_ctax:
                self.__pr(len(meth.especes),*sizes[1])
            else:
                self.__pr(espace.mctax(meth),*sizes[1])
            self.__pr(get_rapp(espace.rtax(meth)) if algo_ctax else "",
                      *sizes[2])
            for j,meth2 in enumerate(espace):
                self.index(10,j)
                if j>i:
                    self.__pr(get_rapp(fn(meth,meth2)),*sizes[3])
                else:
                    self.__pr("",*sizes[3])
                self.index(11,j)
            self.index(6+i%2,i)
            self.nl()

    """
    Affiche la table. Les coefficients sont affichés sous forme de fractions
    si 'fractions vaut True, sous forme de réel sinon.
    """
    def prtable(self,fractions: bool):
        self.__prcommon(fractions,True)

    """
    Affiche la table des match ratio. Les coefficients sont affichés sous forme
    de fractions si 'fractions vaut True, sous forme de réel sinon.
    """
    def prmratio(self,fractions: bool):
        self.__prcommon(fractions,False)

    """
    Affiche la chaîne 'msg. La fonction par défaut l'affiche par print(end=""),
    mais les classes dérivées peuvent redéfinir cette méthode.
    Attention : .print() ne prend en argument qu'une simple chaîne 'msg, non
    une série comme la builtin.
    """
    def print(self,msg: str):
        print(msg,end="")

    """
    Affiche un saut de ligne.
    """
    def nl(self):
        self.print("\n")

    """
    Cette méthode est appelée régulièrement par .prtable() au cours de
    l'affichage de la table. L'indicateur 'what spécifie l'étape ; 'arg dépend
    de 'what.
    La méthode par défaut ne fait rien, mais les classes dérivées peuvent
    redéfinir cette méthode. 'what a l'une des valeurs suivantes
        0   Début d'affichage, avant la première ligne de titre.
        1   Fin de la ligne de titre.
        2   Début de la ligne d'en-têtes de colonnes (noms des méthodes).
        3   Fin de la ligne d'en-têtes de colonnes.
        Pour chaque ligne de méthode :
        4   Début de la ligne. 'arg est le numéro de la méthode, à compter
            de 0.
        5   Fin de la 1ière colonne (noms des méthodes).
        6,7 Fin de la ligne, alternativement 6 et 7. 'arg est le numéro de la
            méthode, à compter de 0 (le même que pour le début de ligne).
        10  Dans une ligne de type 2 ou 4, début de la méthode de rang 'arg.
        11  Dans une ligne de type 2 ou 4, fin de la méthode de rang 'arg
            (même valeur que pour l'appel 10).  
    """
    def index(self,what: int,arg: Optional[int] =None):
        pass

# -- Lecture des fichiers sources ------------

"""
Les instance de toutes les sous-classes disposent au minimum des attributs et
méthodes suivants :
    .methodes       Liste des Methode. Absent avant le chargement par .load().
    .echantillons   Liste des Echantillon utilisés dans les Methode. Absent
                    avant le chargement par .load().
    .fich           Le nom du fichier source.
    .type           Le type de la source : "spart", "csv", "excel", etc.
    .load()         Au premier appel, lit et charge le fichier, renseigne les
                    attributs .methodes et .echantillons (qui valent None avant
                    le chargement), et rend la liste des Methode. Aux appels
                    suivants, rend simplement la liste des Methode déjà chargée.
"""
class Source:
    methodes: List[Methode]
    echantillons: List[Echantillon]
    type: str
    fich: str
    if TYPE_CHECKING:
        def load(self) -> List[Methode]:...
