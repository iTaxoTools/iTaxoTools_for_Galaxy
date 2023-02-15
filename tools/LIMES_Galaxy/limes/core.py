## -*- coding:Latin-1 -*-

"""
D�finit les classes et fonctions suivantes :

    Espace()
    Printer()

Les m�thodes de Esapce permettent de calculer les diff�rents indices Ttax, Ctax,
Mtax. Les fonctions de base pour calculer ces indices sont union() et
intersection(). La fonction communes() sert � calculer les partitions (voir
module "partition").

Printer() produit la repr�sentation format�e qui peut �tre affich�e dans
l'interface (voir wlimes) ou produite dans un fichier ou � l'�cran.
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
Rend la langue courante, �ventuellement apr�s l'avoir affect�e � 'lg si !=None.
"""
def set_langue(lg: Optional[int] =None) -> int:
    global _langue
    if lg is not None:
        _langue=lg
    return _langue

MLMsgType=Sequence[str]

"""
Les arguments donnent les messages �quivalents dans les diff�rentes langues
support�es. Dans la version actuelle : fran�ais, anglais.
Rend le message (�l�ment de 'msgs) correspondant � la langue courante.
"""
def get_text(*msgs:str) -> str:
    return msgs[_langue]

# -- Utilitaires ------------

class RedundantNameError(ValueError):
    pass

class EmptyMethodError(ValueError):
    pass

CodeEspeceType=Union[int,str]

# -- M�thodes ------------

NOM=attrgetter("nom")

"""
Echantillon(nom)

Repr�sente un �chantillon = specimen.

L'instance est hashable, et l'�galit� avec les autres instances de Echantillon
repose sur .nom.

Attributs :
    .nom    Nom fourni � la cr�ation.
"""
class Echantillon:
    def __init__(self,nom: str):
        self.nom=nom

    def __repr__(self):
        return "%s(%s)"%(self.__class__.__name__,self.nom)

    def __str__(self):
        return self.nom

    # Les m�thodes __hash__() et __eq__() sont utiles pour mettre les
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
esp�ce associ� � chacun, extrait d'une colonne du tableau source, dans l'ordre
de ce tableau. Les �l�ments de 'codesespeces sont de type quelconque (int,
str). Les Methode sont cr��es par les readers. 'source est l'instance de Source
� laquelle appartient la m�thode.

L'instance est le dictionnaire donnant pour chaque Echantillon son code esp�ce.

L'instance dispose des attributs et m�thodes suivants :
    .nom        Nom fourni � la cr�ation.
    .especes    Liste des esp�ces : il s'agit d'un dictionnaire (non ordonn�) :
                la clef est le code d'esp�ce, la valeur le set des Echantillon.
                len(self.especes) est donc le nombre d'esp�ces identifi�es par
                la m�thode.
    .source     L'instance de Source � laquelle appartient la Methode.
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
        # On pourrait ajouter le test que le nombre d'�chantillons est >=1.
        # Pour le moment, ceci est inutile car le test a toujours �t� r�alis�
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
    # Le pEchantillon doit �tre hashable, et la comparaison bas�e sur le nom,
    # pour la comparaison avec un RefEchantillon dans test_limes (par ex. :
    # test_partitions.exec_test()).
    # La hashabilit� est h�rit�e de Echantillon.

    # Dans un Espace, il y a toujours 1 seul pEchantillon portant un nom
    # donn�. Les pEchantillon peuvent dont toujours �tre compar�s par
    # l'identit�. D�s lors, il n'ont pas besoin de __eq__() ni de __hash__() :
    # les fonctions de object suffisent, et sont plus efficaces. Cependant,
    # ces fonctions sont h�rit�es de Echantillon -> peut-�tre n'y a-t-il pas
    # d'utilit� � ce que pEchantillon d�rive de Echantillon.

PaquetType=Collection[Echantillon]
EspeceType=Mapping[CodeEspeceType,PaquetType]
PaquetListeType=Collection[PaquetType]

"""
pMethode(meth,mdict,an)

Une pMethode repr�sente une Methode dans un Espace. Elle est �quivalente �
la Methode d'origine, mais les �chantillons sont repr�sent�s par des
pEchantillon au lieu des Echantillon ; les pEchantillon ont �t� normalis�s
entre les diff�rentes m�thodes de l'Espace.

La pMethode peut comprendre :
    - moins d'�chantillons que l'Espace dans lequel elle a �t� cr��e, si
        d'autres m�thodes contiennent des �chantillons absent de 'meth.
    - moins d'�chantillons que 'meth, si l'Espace a �t� cr�� avec l'option
        common=True, et que les �chantillons non communs ont �t� exclus.

'meth est la Methode d'origine. 'mdict est un dictionnaire {nom: pEchantillon},
donnant l'ensemble des pEchantillon cr��s dans l'espace ; 'nom est le nom du
pEchantillon. 'an est un dictionnaire {old: new} donnant le nom 'new du
pEchantillon correspondant au nom 'old dans la Methode d'origine. 'old et 'new
peuvent �tre diff�rents si les noms des �chantillons ont �t� normalis�s.

Noter que 'mdict peut contenir des �chantillons absents de la Methode (�chan-
tillons pr�sents dans d'autres m�thodes de l'espace), et inversemment (�chan-
tillons non communs � toutes les m�thodes de l'espace). La pMethode cr��e ne
contiendra que les �chantillons communs aux deux.

L'instance est le dictionnaire des pEchantillon. Elle est hashable, et
l'�galit� avec les autres instances de pMethode repose sur .nom.

L'instance dispose des attributs et m�thodes suivants :
    .nom        Egal au nom 'eff_nom pass� � la cr�ation si !=None, ou au nom
                de la Methode 'meth sinon.
    .meth       La Methode 'meth fournie � la cr�ation.
    .especes    Comme meth.especes, mais les �l�ments sont des set de
                pEchantillon et non d'Echantillon.
    .all        Dictionnaire pE -> E, donnant l'Echantillon 'E dans 'meth
                correspondant au pEchantillon 'pE composant l'instance. Pour
                les pEchantillon absents de la pMethode, 'E vaut None. .all
                contient tous les �chantillons de l'Espace dans lequel
                l'instance a �t� cr��e.
    .exclus     Liste des Echantillon de 'meth non repris dans la pMethode,
                ou None s'il n'y en a pas. Des �chantillons ont pu �tre exclus
                si l'Espace a �t� cr�� avec l'option common=True.
    .ctax()

Elle h�rite �galement de tous les attributs de la Methode 'meth, et notamment :
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
            new=an[ech.nom] # hors try: car doit tj �tre pr�sent.
            try:
                pe=mdict.pop(new)
            except KeyError:
                exclus.append(ech)
                # Echantillon exclus, non commun � toutes les Methode.
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
        # Le dictionnaire est calcul� au premier appel, puis stock�.

    def __getattr__(self,attr):
        return getattr(self.meth,attr)

    # Les fonctions __eq__(), __ne__() et __hash__() sont n�cessaires pour
    # l'utilisation dasn un dict, par exemple dans .__ctax. La comparaison est
    # bas�e sur le nom.
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

    # Calcule l'intersection et l'union des �v�nements de sp�ciation entre les
    # deux pMethode 'self et 'm2. Rend le couple (a,b) o� 'a est la liste des
    # groupes de pEchantillon de l'intersection et 'b la liste des groupes
    # de pEchantillon de l'union.
    # Les listes ne sont calcul�es qu'au premier appel et conserv�es pour les
    # appels suivant.
    # Si les listes n'ont pas encore �t� calcul�es, le calcul est r�alis� si
    # 'force vaut True. Si 'force vaut False, le calcul n'est pas r�alis� et la
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
Rend la liste des paquets, c-�-d des groupes (set) de pEchantillon communs �
toutes les pMethode de la liste 'meths. On peut soit fournir les pMethode en
arguments, soit fournir comme unique argument la liste des pMethode.

Pour constituer les paquets :
    - On part d'un paquet constitu� de tous les �chantillons.
    - Pour la premi�re m�thode, on scinde ce paquets en autant d'esp�ces,
        chacun regroupant les �chantillons d'une esp�ce.
    - Pour la 2i�me m�thode, on reprend chacun des paquets, et on le scinde
        en autant de paquets qu'il faut pour que aucun ne contienne des
        �chantillons d'esp�ces diff�rentes de cette m�thode.
    - Pour la 3i�me m�thode, on reprend chacun des paquets que l'on scinde �
        nouveau, et ainsi de suite.
"""
def union(*ameths: Union[pMethode,list[pMethode],Espace]) -> PaquetListeType:
    meths: list[pMethode] = _meths_arg(ameths)

    """
    Pour chaque paquet de la liste 'paqs, analyse s'il doit �tre scind�
    � partir de la constitution de la pMethode 'meth. Rend une nouvelle
    liste de paquets, constitu�e � partir de la premi�re, mais o� certains
    paquets ont pu �tre scind�s en plusieurs.
    """
    def splitpaqs(meth: pMethode,paqs: PaquetListeType)-> PaquetListeType:
        paqs2: List[PaquetType] =[]
        for paq in paqs:
            ll=defaultdict(set)
            for e in paq:
                ll[meth[e]].add(e)
                # 'll est un dict donnant, pour chaque esp�ce � laquelle
                # appartient au moins 1 �chantillon du paquet trait� 'paq,
                # le set des �chantillons appartenant � cette esp�ce. Il
                # faudra donc scinder le paquet en autant de paquets qu'il
                # y a d'esp�ces.
            paqs2.extend(ll.values())
            # Chaque valeur de 'll repr�sente un set d'�chantillons
            # appartenant � une esp�ce distincte selon la m�thode 'meth.
            # Ce set doit donc constituer un paquet distinct. Noter
            # qu'il se peut que tous les �chantillons appartiennent � la
            # m�me esp�ce, auquel cas l'unique nouveau paquet
            # ll.values()[0] est identique au paquet d'origine 'paq.
        return paqs2

    paqs: PaquetListeType =[set(meths[0])]
        # 'paqs est la liste des paquets. On part d'une liste avec un seul
        # paquet, comprenant tous les �chantillons (liste de la premi�re
        # m�thode ; toutes les m�thodes sont suppos�es avoir la m�me liste
        # d'�chantillons, par construction).
    for m in meths:
        paqs=splitpaqs(m,paqs)
            # Pour chaque Methode, splitpaqs() traite la liste courante de
            # paquets et rend une nouvelle liste, constitu�e � partir de la
            # premi�re mais o� certains paquets ont pu �tre scind�s en
            # plusieurs. La liste rendue constitue la liste en entr�e pour
            # le cycle suivant.
    return paqs

"""
Rend la liste des paquets (set) correspondant � l'intersection des �v�nements
de sp�ciation des pMethode de la liste 'meths. On peut soit fournir les
pMethode en arguments, soit fournir comme unique argument la liste des
pMethode.

Pour cr�er un paquet :
    - On prend un �chantillon non encore pris dans un paquet, et on le met dans
        le nouveau paquet.
    - On recherche dans chacune des m�thodes l'esp�ce qui inclut cet
        �chantillon.
    - On ajoute dans le paquet tous les �chantillons constituant cette esp�ces.
    - Quand on a parcouru toutes les m�thodes, on recommence en consid�rant
        chacun des �chantillons qu'on a ajout� au cycle pr�c�dent, qui peuvent
        ainsi attirer d'autres esp�ces.
    - On a fini le paquet quand le parcours des m�thodes n'ajoute plus de
        nouvel �chantillon.
"""
def intersection(*ameths: Union[pMethode,list[pMethode]]) -> PaquetListeType:
    meths: list[pMethode] = _meths_arg(ameths)
    pool=set(meths[0]) # pool = ensemble de tous les �chantillons
    inter: List[PaquetType] =[]
    while pool:
        paq=set()
        paq.add(pool.pop())
        # On prend un �chantillon restant, on le place dans 'paq, puis on va
        # chercher la fermeture transitive � partir de celui-ci.
        nb=0
        while nb!=len(paq):
            # On reboucle sur les m�thode tant que le traitement a ajout� un
            # �chantillon -> fermeture transitive.
            nb=len(paq)
            for m in meths:
                for e in list(paq): # list() car le 'paq est modifi� ensuite.
                    # Remarque : on reprend ici tous les �chantillons dans le
                    # paquet. En th�orie, on pourrait optimiser en ne consid�-
                    # rant que les �chantillons ajout�s au cycle while
                    # pr�c�dent. Noter cependant que chaque m�thode "profite"
                    # des �chantillons ajout�s dans le m�me cycle while pour
                    # les m�thodes pr�c�dentes.
                    for p in m.especes.values():
                        if e in p:
                            paq.update(p)
                            break
                            # break parce qu'un �chantillon ne peut se trouver
                            # que dans une esp�ce et une seule.
        inter.append(paq)
        pool.difference_update(paq)
    return inter

"""
Rend la liste des esp�ces communes � toutes les pMethode de la liste 'meths,
c-�-d les esp�ces constitu�es des m�mes pEchantillon. Les esp�ces rendues sont
constitu�es du set des pEchantillon. La liste rendue n'est pas ordonn�e, mais
est consistante (l'ordre sera toujours le m�me avec la m�me liste de m�thodes).
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

Cr�e l'espace combinant toutes les Methode de la liste 'meths. Chaque Methode
est repr�sent�e par une pMethode. Le Espace est le tuple de ces pMethode,
dans le m�me ordre que 'meths.

Dans les pMethode, les Echantillon sont remplac�s par des pEchantillon. Toutes
les pMethode du Espace partagent le m�me jeu de pEchantillon ; l'�galit� est
donc assimilable � l'identit� ("is" peut �tre utilis� � la place de ==, ce qui
est plus efficace).

Si 'strict vaut True, les Echantillon sont identifi�s entre les Methode par
leur nom exact. Si 'strict vaut False, les noms des Echantillon sont norma-
lis�s : la casse est forc�e en minuscule, et toutes les s�quences de caract�res
sp�ciaux sont remplac�es par un '_'. C'est sous ce nom normalis� que sont
faites les correspondances entre les Methode, et ce sera aussi le nom des
pEchantillon. G�n�re une exception RedundantNameError si deux �chantillons
d'une m�me Methode portent le m�me nom apr�s normalisation.

Si 'common vaut False, les pMethode comporteront la m�me liste d'�chantillons
que la Methode d'origine. Si 'common vaut True, seuls sont pris en compte les
�chantillons communs � toutes les Methode. Les pMethode ne comporteront alors
que ces �chantillons communs ; leur attribut .exclus donne la liste des
�chantillons ainsi exclus. L'attribut .meth_modif comptabilise les m�thodes
dont on a ainsi exclus des �chantillons. Une exception EmptyMethodError est
g�n�r�e s'il n'y a aucun �chantillon commun.

L'instance dispose des attributs et m�thodes suivants :
    .echantillons   La liste des pEchantillon. Ils sont tous r�f�renc�s par
                    au moins une pMethode. Si 'common vaut True, il ne s'agit
                    que des �chantillons communs, qui sont alors tous
                    r�f�renc�s par toutes les pMethode.
    .nbech          Nombre d'�chantillons.
    .meth_modif     Nombre de m�thodes dont certains �chantillons ont �t�
                    exclus par l'option 'common (forc�ment 0 si 'common vaut
                    False).
    .exclus         Nombre d'�chantillons exclus si common=True (0 si False).
    .paquets        Liste des paquets, c-�-d des groupes (set) de pEchantillon
                    communs � toutes les pMethode.
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
    Le fonction de normalisation des noms d'�chantillon si 'strict==False.
    """
    @staticmethod
    def normalise(nom):
        return Espace.rex.sub("_",nom.lower())

    def __new__(cls,meths: list[Methode],strict: bool=True,common: bool=False) \
                                                                    -> Espace:
        echs: DefaultDict[str,int] =defaultdict(int)
        # nouveau nom -> nombre de Methode contenant cet �chantillon
        andict: dict[str,str]={}
        # ancien nm -> nouveau nom d'�chantillon
        cptmeth: DefaultDict[str,int] =defaultdict(int)
        # nom de m�thode -> nombre de m�thodes portant ce nom
        for m in meths:
            cptmeth[m.nom]+=1
            mechs=set()
            for e in m:
                old=e.nom
                new=old if strict else Espace.normalise(old)
                if new in mechs:
                    raise RedundantNameError(
                        get_text("M�thode %s: �chantillons %s redondant "
                                 "apr�s normalisation",
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
                get_text("Pas d'�chantillons communs entre toutes les m�thodes",
                         "No common samples between all methods"))

        # Renommage des noms de m�thodes.
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

        me=super().__new__(cls,cast(list,lstpm)) # cast n�cessaire ?
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
    Rend le Rtax de la m�thode 'meth, sous la forme d'un triplet (a,b,c)
    comme suit :
        a = num�rateur (int) = nb. d'�v�nements de sp�ciation identifi�s par la
            m�thode.
        b = d�nominateur (int) = nb. d'�v�nements de sp�ciations pour toutes
            les m�thodes de l'espace (union).
        c = a/b (float) ; None si 'b vaut 0.
    """
    def rtax(self,meth: pMethode) -> IndiceType:
        n=len(meth.especes)-1
        d=len(self.paquets)-1
        return (n,d,(n/d if d else None))

    """
    Rend un it�rateur donnant la liste des pMethode de l'espace tri�es par leur
    nom .nom.
    """
    def sorted(self) -> Iterator[pMethode]:
        yield from sorted(self,key=NOM)
            
    """
    Rend un it�rateur retournant le Rtax pour toutes les m�thodes de l'espace,
    sous la forme de couples (m,(a,b,c)), o� 'm est la pMethode et (a,b,c) le
    Rtax de cette m�thode exprim� comme dans .rtax(). Les �l�ments retourn�s
    sont tri�s par ordre alphab�tique des noms de m�thodes.
    """
    def irtax(self) -> Iterator[tuple[pMethode,IndiceType]]:
        for m in self.sorted():
            yield (m,self.rtax(m))

    """
    Rend le Ctax associ� au couple de m�thodes 'meth1 / 'meth2, sous la forme
    d'un triplet (a,b,c) comme suit :
        a = num�rateur (int) = nb. d'�v�nements de sp�ciation communs aux
            deux m�thodes (intersection).
        b = d�nominateur (int) = nb. d'�v�nements de sp�ciations identifi�s
            par l'une ou l'autre m�thode (union).
        c = a/b (float), ou None si 'b vaut 0.
    """
    @staticmethod
    def ctax(meth1: pMethode,meth2: pMethode) -> IndiceType:
        i,u=meth1.ctax(meth2,False) or meth2.ctax(meth1,False) or \
                                                             meth1.ctax(meth2)
        # On regarde d'abord si le calcul a d�j� �t� fait sur 'meth1 puis
        # 'meth2 ; si non, on force le calcul sur 'meth1.
        ni=len(i)-1
        nu=len(u)-1
        f=ni/nu if nu else None
        return (ni,nu,f)

    """
    Rend un it�rateur retournant le Ctax pour tous les couples de m�thodes de
    l'espace, sous la forme de triplet (m1,m2,(a,b,c)), o� 'm1 et 'm2 sont les
    m�thodes et (a,b,c) le Ctax de ce couple exprim� comme dans .ctax(). Les
    �l�ments retourn�s sont tri�s par ordre alphab�tique de 'm1 puis de 'm2.
    """
    def ictax(self) -> Iterator[tuple[pMethode,pMethode,IndiceType]]:
        for m1,m2 in combinations(self.sorted(),2):
            yield (m1,m2,self.ctax(m1,m2))

    """
    Calcule la moyenne des ctax entre la m�thode 'meth est les autres m�thodes
    de l'espace. Rend cette moyenne sous forme de float, ou None si la moyenne
    n'a pas de sens (pas d'autres m�thodes avec laquelle le Ctax avec 'meth a
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
    Rend le match ratio associ� au couple de m�thodes 'meth1 / 'meth2, sous la
    forme d'un triplet (a,b,c) comme suit :
        a = num�rateur (int) = nb. d'esp�ces identiques entre les deux m�thodes.
        b = d�nominateur (int) = somme des nb. d'esp�ces des deux m�thodes.
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
    Rend un it�rateur retournant le match ratio pour tous les couples de
    m�thodes de l'espace, sous la forme de triplet (m1,m2,(a,b,c)), o� 'm1 et
    'm2 sont les noms des m�thodes et (a,b,c) le match ratio de ce couple
    exprim� comme dans .match_ratio(). Les �l�ments retourn�s sont tri�s par
    ordre alphab�tique de 'm1 puis de 'm2.
    """
    def imatch_ratio(self) -> Iterator[tuple[pMethode,pMethode,IndiceType]]:
        for m1,m2 in combinations(self.sorted(),2):
            yield (m1,m2,self.match_ratio(m1,m2))

    """
    Rend la liste des esp�ces communes � toutes les Methode dont la liste est
    pass�e en argument, c-�-d les esp�ces constitu�es des m�mes �chantillons.
    Les esp�ces rendues sont constitu�es du tuple ordonn� des Echantillon. La
    liste rendue n'est pas ordonn�e, mais est consistante (l'ordre sera
    toujours le m�me avec la m�me liste de m�thodes).
    """
    communes=staticmethod(communes)

"""
Printer(espace)

Le Printer facilite l'affichage des coefficients. 'espace est le Espace �
afficher. L'utilisateur peut subclasser Printer et red�finir les m�thodes
.print() et .index().

Le Printer dispose des attributs et m�thodes suivants :
    .avec_alias Si True, les noms des m�thodes sont trop longs et seront
                substitu�s par des codes dans les en-t�tes de lignes et de
                colonnes. Si False, les noms de m�thodes sont courts et ne
                seront pas substitu�s.
    .codes      It�rable donnant la liste des libell�s affich�s, dans l'ordre
                de 'espace. Il s'agit d'une liste de codes de substitution si
                .avec_alias vaut True, des noms .nom des m�thodes sinon.
    .espace     L'argument 'espace pass� � la cr�ation.
    .pralias()
    .prtable()
    .nl()

La classe peut �tre d�riv�e pour afficher ailleurs qu'� l'�cran. La classe
d�riv�e peut red�finir les m�thodes suivantes :
    .print()
    .index()
"""
class Printer:
    MAXMNAME=6  # nb. max de caract�res d'une m�thode.
    NBDEC=2     # nb. de d�cimales des rapports.

    def __init__(self,espace: Espace):
        self.espace=espace
        self.codes=[NOM(m) for m in espace]
        ln=max(map(len,self.codes))
        self.avec_alias=ln>self.MAXMNAME
        if self.avec_alias:
            nb=len(espace)
            fmt="M%%0%dd"%(1 if nb<10 else (2 if nb<100 else 3))
            self.codes=[fmt%m for m,a in enumerate(self.codes,start=1)]
        # Si un nom de m�thode d�passe MAXMNAME caract�res, on cr�e des codes
        # artificiels ; .avec_alias vaut alors True (False sinon).
        # .codes donne la liste des noms de m�thodes � afficher, dans le m�me
        # ordre que l'Espace. Si .avec_alias vaut False, ce sont les noms
        # (.nom) des Methode. Si .avec_alias vaut True, ce sont des codes
        # g�n�r�s artificiellement.

        sz0=max(map(len,self.codes))
                # Colonne 0 : longueur max d'un code ou nom de m�thode.
        szA1=len("%d"%max(map(len,map(attrgetter("especes"),espace))))
                # Long. max du nombre d'�chantillons dans une esp�ce.
        szA2=7  # Longueur max d'un rapport A/B. On suppose qu'il y aura au
                # plus 999 �chantillons -> 3+3+1 car.
        szA3=szA2
        szB1=self.NBDEC+2
                # Long. d'un flottant < 1, avec NBDEC d�cimales.
        szB2=szB1
        szB3=szB1
        sz1=max(szA1,szB1,5)
                # La colonne 1 contient les nb. d'�chantillons par esp�ce
                # (szA1), des flottant<1 (avec NBDEC d�cimales) (szB1), et le
                # mot "mCtax".
        sz2=max(szA2,szB2,4)
                # La colonne 2 contient des rapports (szA2), des flottants<1
                # (szB2), et le mot "Rtax".
        sz3=max(szA3,szB3,4,sz0)
                # Les colonnes 3 contiennent des rapports (szA3), des flottants
                # (szB3), le mot "Ctax", et les codes/noms des m�thodes (sz0).
        bl0=4 # Blancs s�parateurs avec la colonne suivante.
        bl1=2
        bl2=2
        bl3=2
        self.__sizes=((sz0,bl0),(sz1,bl1),(sz2,bl2),(sz3,bl3))
        # Chaque �lement correspond � une colonne : colonne 0 (noms des
        # m�thodes), colonne 1 (Esp/mCtax), colonne 2 (Rtax), colonnes 3
        # (colonnes des Ctax, table proprement dite).
        # Chaque �lement est un couple (a,b), o� 'a est la largeur de la
        # colonne, et 'b le nombre de blancs qui la s�parent de la colonne
        # suivante.

    """
    Affiche 'a sur une zone de 'sz caract�res, cadr� � droite, suivi de 'bl
    blancs. 'a a l'un des format suivant :
        - str : cha�ne
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
    Si les m�thodes ont d� �tre renomm�es, affiche la table de correspondance
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
    Affiche la table. Les coefficients sont affich�s sous forme de fractions
    si 'fractions vaut True, sous forme de r�el sinon.
    """
    def prtable(self,fractions: bool):
        self.__prcommon(fractions,True)

    """
    Affiche la table des match ratio. Les coefficients sont affich�s sous forme
    de fractions si 'fractions vaut True, sous forme de r�el sinon.
    """
    def prmratio(self,fractions: bool):
        self.__prcommon(fractions,False)

    """
    Affiche la cha�ne 'msg. La fonction par d�faut l'affiche par print(end=""),
    mais les classes d�riv�es peuvent red�finir cette m�thode.
    Attention : .print() ne prend en argument qu'une simple cha�ne 'msg, non
    une s�rie comme la builtin.
    """
    def print(self,msg: str):
        print(msg,end="")

    """
    Affiche un saut de ligne.
    """
    def nl(self):
        self.print("\n")

    """
    Cette m�thode est appel�e r�guli�rement par .prtable() au cours de
    l'affichage de la table. L'indicateur 'what sp�cifie l'�tape ; 'arg d�pend
    de 'what.
    La m�thode par d�faut ne fait rien, mais les classes d�riv�es peuvent
    red�finir cette m�thode. 'what a l'une des valeurs suivantes
        0   D�but d'affichage, avant la premi�re ligne de titre.
        1   Fin de la ligne de titre.
        2   D�but de la ligne d'en-t�tes de colonnes (noms des m�thodes).
        3   Fin de la ligne d'en-t�tes de colonnes.
        Pour chaque ligne de m�thode :
        4   D�but de la ligne. 'arg est le num�ro de la m�thode, � compter
            de 0.
        5   Fin de la 1i�re colonne (noms des m�thodes).
        6,7 Fin de la ligne, alternativement 6 et 7. 'arg est le num�ro de la
            m�thode, � compter de 0 (le m�me que pour le d�but de ligne).
        10  Dans une ligne de type 2 ou 4, d�but de la m�thode de rang 'arg.
        11  Dans une ligne de type 2 ou 4, fin de la m�thode de rang 'arg
            (m�me valeur que pour l'appel 10).  
    """
    def index(self,what: int,arg: Optional[int] =None):
        pass

# -- Lecture des fichiers sources ------------

"""
Les instance de toutes les sous-classes disposent au minimum des attributs et
m�thodes suivants :
    .methodes       Liste des Methode. Absent avant le chargement par .load().
    .echantillons   Liste des Echantillon utilis�s dans les Methode. Absent
                    avant le chargement par .load().
    .fich           Le nom du fichier source.
    .type           Le type de la source : "spart", "csv", "excel", etc.
    .load()         Au premier appel, lit et charge le fichier, renseigne les
                    attributs .methodes et .echantillons (qui valent None avant
                    le chargement), et rend la liste des Methode. Aux appels
                    suivants, rend simplement la liste des Methode d�j� charg�e.
"""
class Source:
    methodes: List[Methode]
    echantillons: List[Echantillon]
    type: str
    fich: str
    if TYPE_CHECKING:
        def load(self) -> List[Methode]:...
