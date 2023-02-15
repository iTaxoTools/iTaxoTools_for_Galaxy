
from __future__ import annotations

import re,datetime,sys
from .core import (Echantillon,Methode,Source,RedundantNameError,get_text,
                   Espace)
from .core import MLMsgType

from operator import itemgetter

from typing import (Optional,Any,Pattern,Match,Set,Tuple,Type,Union,cast,
                    TextIO,List,Callable,TypeVar,Dict,overload)

# -----------------------------------------------------------
# Utilitaires.

SectionType=Optional[str]
NumligneType=Optional[int]
LigneType=Tuple[int,str]
LignesType=List[LigneType]
ScoreType=Optional[float]

"""
Rend le message d'erreur formé en utilisant le titre de section 'sec, le numéro de
ligne 'num, le message 'msgs, avec ses paramètre 'args (façon printf()). 'sec
et/ou 'num peuvent valoir None si la valeur n'est pas connue. 'msgs est un
tuple de messages (français, anglais).
"""
def msgError(sec: SectionType,num: NumligneType,msgs: MLMsgType,*args: Any)\
                                    -> str :
    lst=[]
    if num is not None: lst.append(str(num))
    if sec is not None: lst.append(sec)
    if lst: m="[%s] "%", ".join(lst)
    else: m=""
    return m+(get_text(*msgs)%args)

"""
Matche la ligne 'lg contre la RE 'rex. Si ok, rend l'instance de matching.
Sinon, génère une exception SyntaxError (voir msgError() pour 'sec, 'num, 'msg
et 'args). 'msg est le couple des messages d'erreur ; le texte de la ligne 'lg
lui est automatiquement ajouté.
"""
def match(sec: SectionType,num: NumligneType,rex: Pattern,lg: str,
          msg: MLMsgType) -> Match:
    ma=rex.fullmatch(lg)
    if ma: return ma
    raise SyntaxError(msgError(sec,num,[m+" <%s>" for m in msg],lg))

"""
Concatène toutes les lignes de la liste 'lst, en séparant chacune par un blanc.
Rend le couple (a,b) où 'a est le numéro de la première ligne, et 'b la ligne
concaténée.
"""
def lignesaplat(lst: LignesType) -> tuple[int,str]:
    num=lst[0][0]
    return num," ".join(e[1] for e in lst)

@overload
def get_int(sec: SectionType,num: NumligneType,mot: str,msg: MLMsgType,*,
            interog: bool) -> Optional[int]: ...

@overload
def get_int(sec: SectionType,num: NumligneType,mot: str,msg: MLMsgType,*,
            min: int) -> int: ...

# 'mot est un entier sous forme textuelle. Rend la valeur numérique (int)
# correspondante. Contrôle que cette valeur est >=min. Si 'interog vaut True,
# accepte aussi que 'mot soit réduit à un point d'interrogation, et rend None
# dans ce cas. 'mot peut comprendre des blancs avant et après.
# Si erreur, génère une exception SyntaxError ou ValueError (voir msgError()
# pour 'sec, 'num, msg) ; le mot 'mot est autmatiquement ajouté dans le message.
#
def get_int(sec: SectionType,num: NumligneType,mot: str,msg: MLMsgType,*,
            interog: bool =False,min: int =0) -> Optional[int]:
    mot=mot.strip()
    exc: Type[Exception]
    if interog and mot=="?": return None
    try:
        i=int(mot)
    except:
        exc=SyntaxError
    else:
        if i<min:
            exc=ValueError
        else:
            return i
    raise exc(msgError(sec,num,[m+" <%s>" for m in msg],mot))

@overload
def split_2points(sec: SectionType,num: NumligneType,lg: str,
                  msg: MLMsgType,*,isnum: bool,strict: bool) \
                  -> tuple[int,Optional[str]]: ...

@overload
def split_2points(sec: SectionType,num: NumligneType,lg: str,
                  msg: MLMsgType,*,isnum: bool) \
                  -> tuple[int,str]: ...

@overload
def split_2points(sec: SectionType,num: NumligneType,lg: str,msg: None) \
                  -> tuple[str,str]: ...

# Contrôle que la ligne 'lg est formée de 2 parties séparées par ':'. Rend le
# couple (a,b) où 'a et 'b sont la première et la deuxième partie respectivement,
# stripées. La première partie est numérique si 'isnum vaut True, auquel cas 'a
# est le int correspondant, qui doit être >0.
# Si 'strict vaut False, accepte que le ':' et la seconde partie soient absents ;
# 'b vaut None dans ce cas.
# Les blancs en tête et en queue sont ignorés.
# Si erreur, génère une exception SyntaxError (voir msgError() pour 'sec, 'num).
# 'msg est un couple de messages d'erreur décrivant le 1er terme, utilisé
# seulement si 'isnum vaut True : exemple : ("Nom invalide","Invalid name") ;
# 'msg est ignoré si 'isnum vaut False.
#
def split_2points(sec: SectionType,num: NumligneType,lg: str,
                  msg: Optional[MLMsgType],*,
                  isnum: bool =False,strict: bool =True) \
                  -> tuple[Union[int,str],Optional[str]]:
    ett,dp,lg=lg.partition(':')
    ret: Optional[str]
    if dp:
        ret=lg.strip()
    else:
        if strict:
            raise SyntaxError(msgError(sec,num,("':' absent","':' is missing")))
        ret=None
    if isnum:
        assert msg is not None
        return (get_int(sec,num,ett,msg,min=1),ret)
    return (ett.strip(),ret)

"""
'mot est un score sous forme textuelle. Rend la valeur numérique (float)
correspondante. La valeur est quelconque. Accepte aussi que 'mot soit réduit à
un point d'interrogation, et rend None dans ce cas. 'mot peut comprendre des
blancs avant et après.
Si erreur, génère une exception SyntaxError (voir msgError() pour 'sec et
'num).
"""
def get_score(sec: SectionType,num: NumligneType,mot: str) -> ScoreType:
    mot=mot.strip()
    if mot=="?":
        return None
    try:
        return float(mot)
    except:
        raise SyntaxError(msgError(sec,num,("Score invalide <%s>",
                                            "Invalid score <%s>"),
                                   mot))

"""
Contrôle la cohérence de la présence ou absence d'un score. 'avecsc vaut True
si un score est attendu, False si un score est interdit, None si on ne sait pas
encore. 'sc est la donnée score, qui vaut None ou non (contenu quelconque dans
ce cas).
Contrôle que 'sc est cohérent avec 'avecsc, c-à-d 'sc==None si 'avecsc==False
ou 'sc!=None si 'avecsc==True. Au retour, rend la valeur True/False définitive
de 'avecsc : égale à la valeur en entrée si elle était True ou False,
déterminée selon 'sc si elle valait None.
Génère une Exception SyntaxError si 'avecsc et 'sc sont incohérents.
"""
def get_avecsc(sec: SectionType,num: NumligneType,avecsc: Optional[bool],
               sc: Optional[str]) -> bool:
    if avecsc is None:
        avecsc=sc is not None
    else:
        if (avecsc if sc is None else not avecsc):
            raise SyntaxError(msgError(sec,num,
                                ("Absence/présence des scores incohérente",
                                 "Inconsistent absence/presence of scores")))
    return avecsc

sn_rex=re.compile(r"\w+",re.ASCII)

"""
Contrôle que 'nom est un nom d'échantillon valide. Si ok, rend le nom stripé.
Si ko, génère une exception SyntaxError.
"""
def is_sample_name(sec: SectionType,num: NumligneType,nom: str) -> str:
    nom=nom.strip()
    if sn_rex.fullmatch(nom):
        return nom
    raise SyntaxError(msgError(sec,num,
                               ("Nom d'échantillon invalide <%s>",
                                "Invalid sample name <%s>"),nom))

"""
Contrôle que 'nom est un nom de partition valide. Si ok, rend le nom stripé.
Si ko, génère une exception SyntaxError.
"""
def is_partition_name(sec: SectionType,num: NumligneType,nom: str) -> str:
    nom=nom.strip()
    ok=True
    if nom and nom.isascii():
        for c in nom:
            if not (c.isalnum() or c in "!\"#$%&'()*+-.<=>?@\\^_`{|}"):
                ok=False
                break
    else:
        ok=False
    if not ok:
        raise SyntaxError(msgError(sec,num,
                                   ("Nom de spartition <%s> invalide",
                                    "Name of the spartition <%s> invalid"),
                                   nom))
    return nom

"""
Contrôle que le nom 'nom n'est pas redondant. 'stock est le stock des noms
déjà vus. Génère une exception RedundantNameError si 'nom a déjà été vu (casse
insensible). Sinon, ajoute 'nom dans 'stock. 'label est le type d'objet, qui
sera utilisé dans le message d'erreur. 'label est une liste (français, anglais).
"""
def ctrl_redond(sec: SectionType,num: NumligneType,nom: str,stock: Set[str],
                label: MLMsgType):
    nm2=nom.lower()
    if nm2 in stock:
        label=get_text(*label)
        raise RedundantNameError(msgError(sec,num,
                                  ("Nom de %s redondant <%%s>"%label,
                                   "Redundant name of %s <%%s>"%label),
                                  nom))
    stock.add(nm2)

# -----------------------------------------------------------
# Lecture d'un bloc.

re_titre=re.compile(r"\s*(\w+)\s*=\s*(.*?)\s*",re.ASCII)

"""
Lit le prochain bloc dans le fichier 'file. 'num est le numéro de la dernière
ligne lue (utile pour les messages d'erreur ; donner 0 pour la lecture du
premier bloc).
Rend un triplet (num,tt,lst), où 'num est le numéro de la dernière ligne lue,
'tt le titre du bloc, et 'lst la liste des couples (n,t) des lignes constituant
le bloc ('n est le numéro de ligne et 't la ligne).
Les lignes 't restituées ont les propriétés suivantes :
    - les commentaires ont été éliminés ; les commentaires inclus ont été
        remplacés par un blanc (ils sont donc séparateurs).
    - les lignes vides (éventuellement après élimination des commentaires) ont
        été éliminées.
    - les lignes sont stripées au début et à la fin.
Cas particuliers :
    - Rend (None,None,None) s'il n'y a plus de blocs dans le fichier.
    - Rend (num,"begin",None) pour le bloc "begin spart".
    - Rend (num,"end",None) pour le bloc "end".
Génère une exception SyntaxError si erreur.
"""
def read_bloc(file: TextIO,num: int) -> \
                        Union[Tuple[None,None,None],
                        Tuple[int,str,Optional[LignesType]]]:
    lst=[]
    outcomm=True
    num+=1
    for num,lg in enumerate(file,start=num):
        ll=[]
        while True:
            t,s,lg=lg.partition("]["[outcomm])
            if outcomm:
                ll.append(t)
            if not s:
                break
            outcomm=not outcomm
        lg=" ".join(ll)
        end=';' in lg
        if end:
            lg,_,q=lg.partition(';')
            if q.strip():
                raise SyntaxError(msgError(None,num,("Ligne non vide après ';'",
                                                     "Line not empty after ';'")))
        lg=lg.strip()
        if lg:
            lst.append((num,lg))
        if end:
            break
    else:
        if lst:
            raise SyntaxError(get_text("Dernier bloc non terminé par ';'",
                                       "Last block not ended with ';'"))
        return (None,None,None)
    if not lst:
        raise SyntaxError(msgError(None,num,("Bloc vide","Empty block")))
    # A partir d'ici, 'lst contient uniquement les lignes non vides, stripées,
    # et débarassées des commentaires et du ';' final.

    if len(lst)<=2:
        lg=" ".join(" ".join(map(itemgetter(1),lst)).split())
        if lg=="begin spart":
            return (num,"begin",None)
        if lg=="end":
            return (num,"end",None)

    n1,lg=lst.pop(0)
    n2=None
    if '=' not in lg and lst:
        n2,lg2=lst.pop(0)
        lg+=lg2
    ma=match(None,n1,re_titre,lg,("Ligne de titre mal formée",
                                  "Malformed title line"))
    titre,q=ma.groups()
    if q:
        lst.insert(0,(n2 or n1,q))
    if not lst:
        raise SyntaxError(msgError(titre,num,("Bloc vide","Empty block")))
    return (num,titre,lst)

# -----------------------------------------------------------
# Lecture de chaque type de bloc.

"""
Lit un bloc "Project_name" et rend le titre.
Génère une exception SyntaxError si erreur.
"""
def read_Project_name(sec: str,lst: LignesType) -> str:
    num,lg=lignesaplat(lst)
    lg=lg.strip()
    if lg: return lg
    raise SyntaxError(msgError(sec,num,("Titre vide","Empty title")))
    # Normalement, ne peut survenir car le bloc vide aura été détecté par
    # read_bloc().

"""
Lit un bloc "Date" et rend le datetime correspond.
Génère une exception SyntaxError si la date est mal formée.
"""
def read_Date(sec: str,lst: LignesType) -> datetime.datetime:
    num,lg=lignesaplat(lst)
    lg=lg.strip()
    try:
        return datetime.datetime.fromisoformat(lg)
    except ValueError:
        raise SyntaxError(msgError(sec,num,("Date invalide","Invalid date")))

"""
Lit un bloc "N_spartitions" et rend une liste comportant un élément par
spartition. Chaque élément est de la forme (a,b) où 'a est le nom de la
spartition et 'b son score (ou None). On a la garantie que les noms des
spartitions sont uniques (casse non sensible).
Génère une exception SyntaxError ou ValueError si erreur, RedundantNameError si
deux partitions ont le même nom.
"""
def read_N_spartitions(sec: str,lst: LignesType) \
                            -> List[Tuple[str,ScoreType]]:
    num,lg=lignesaplat(lst)
    nb,lg=split_2points(sec,num,lg,("Nombre de partitions mal formé",
                                    "Malformed number of spartitions"),
                        isnum=True)
    llg=lg.split('/')
    if len(llg)!=nb:
        raise ValueError(msgError(sec,num,
                    ("Le nombre de partitions ne correspond pas (%d <> %d)",
                     "The number of partitions does not match (%d <> %d)"),
                                  nb,len(llg)))
    part=[]
    dejavu: Set[str] =set()
    avecsc=None
    sc: Optional[str]
    for p in llg:
        nom,sep,sc=p.partition(',')
        nom=is_partition_name(sec,num,nom)
        ctrl_redond(sec,num,nom,dejavu,("spartition","spartition"))
        if not sep: sc=None
        avecsc=get_avecsc(sec,num,avecsc,sc)
        part.append((nom,get_score(sec,num,cast(str,sc)) if avecsc else None))
    return part

"""
Lit un bloc "N_individuals" et rend la liste du nombre d'échantillons pour
chaque spartition.
Génère une exception SyntaxError si erreur.
"""
def read_N_individuals(sec: str,lst: LignesType) -> List[int]:
    num,lg=lignesaplat(lst)
    return [get_int(sec,num,s,("Nombre d'échantillons invalide",
                                    "Invalid number of samples"),
                         min=1)
            for s in lg.split('/')]

"""
Lit un bloc "N_subsets" et rend une liste dont chaque élément correspond à
une spartition ; chaque élément est la liste des scores (float ou None) des
différentes espèces délimitées pour cette spartition ; les listes ont des
longueurs différentes car chaque spartition définit un nombre différent
d'espèces.
Génère une exception SyntaxError ou ValueError si erreur.
"""
def read_N_subsets(sec: str,lst: LignesType) \
                                -> List[List[ScoreType]]:
    num,lg=lignesaplat(lst)
    subs=[]
    avecsc=None
    for s in lg.split('/'):
        ns,lgs=split_2points(sec,num,s,("Nombre de 'subset' mal formé",
                                        "Malformed subset number"),
                             strict=False,isnum=True)
        avecsc=get_avecsc(sec,num,avecsc,lgs)
        if avecsc:
            assert lgs is not None
            llgs=lgs.split(',')
            if len(llgs)!=ns:
                raise ValueError(msgError(sec,num,
                                    ("Subset <%s> : nombre de scores différent",
                                     "Subset <%s>: different number of scores"),
                                          s))
            subs.append([get_score(sec,num,s) for s in llgs])
        else:
            subs.append([None]*ns)
    return subs

T=TypeVar('T',Optional[int],ScoreType)

"""
Traitement commun aux blocs Individual_assignment et Individual_score. 'fn est
la fonction spécifique, appelée avec deux arguments : le numéro de ligne et
un terme sous forme str ; elle doit rendre l'élément à restituer.
"""
def read_Individual_common(sec: str,lst: LignesType,
                           fn: Callable[[int,str],T]) -> \
                           Tuple[int,List[Tuple[str,List[T]]]]:
    output: List[Tuple[str,List[T]]]=[]
    dejavu: Set[str] =set()
    nbpart=0
    for num,lg in lst:
        ech,lg=split_2points(sec,num,lg,None)
        ech=is_sample_name(sec,num,ech)
        ctrl_redond(sec,num,ech,dejavu,("échantillon","sample"))
        llg=lg.split('/')
        n=len(llg)
        if output:
            if n!=nbpart:
                raise ValueError(msgError(sec,num,
                                          ("Nombre de méthodes <%d> incohérent",
                                           "Inconsistent number of methods <%d>"),
                                          n))
        else:
            nbpart=n
        output.append((ech,[fn(num,s) for s in llg]))
    return nbpart,output

"""
Lit un bloc "Individual_assignment" et rend un couple (a,b) où 'a est le nombre
de spartitions et 'b la liste des affectations par échantillon. Chaque élément
est un couple (c,d), où 'c est le nom de l'échantillon et 'd la liste des rangs
de cet échantillon pour chacune des 'a spartitions. Chaque rang est un entier
>=0, ou None s'il n'y a pas d'affectation de cet échantillon pour cette
spartition.
On a la garantie que les noms des échantillons sont uniques (casse non sensible).
Génère une exception SyntaxError ou ValueError si erreur,
RedundantNameError si un échantillon est redondant.
"""
def read_Individual_assignment(sec: str,lst: LignesType) -> \
                        Tuple[int,List[Tuple[str,List[Optional[int]]]]]:
    def read_rank(num: int,rk: str) -> Optional[int]:
        return get_int(sec,num,rk,("Rang invalide","Invalid rank"),interog=True)
    return read_Individual_common(sec,lst,read_rank)

"""
Lit un bloc "Individual_score" et rend un couple (a,b) où 'a est le nombre de
spartitions et 'b la liste des scores par échantillon. Chaque élément est un
couple (c,d), où 'c est le nom de l'échantillon et 'd la liste des scores de
cet échantillon pour chacune des 'a spartitions. Chaque score est un float,
ou None s'il n'y a pas de score pour cet échantillon et cette spartition.
On a la garantie que les noms des échantillons sont uniques.
Génère une exception SyntaxError ou ValueError si erreur,
RedundantNameError si un échantillon est redondant.
"""
def read_Individual_score(sec: str,lst: LignesType) -> \
                        Tuple[int,List[Tuple[str,List[ScoreType]]]]:
    def read_score(num: int,sc: str) -> ScoreType:
        return get_score(sec,num,sc)
    return read_Individual_common(sec,lst,read_score)

"""
Lit un bloc XXX_score_type et rend la liste des noms de types, un par
partition. Le type vaut None s'il n'est pas défini pour cette partition.
"""
def read_Spartition_score_type(sec: str,lst: LignesType) -> List[Optional[str]]:
    num,lg=lignesaplat(lst)
    return [(None if t=="?" else t) for t in
                                        (tt.strip() for tt in lg.split('/'))]

read_Subset_score_type=read_Individual_score_type=read_Spartition_score_type

"""
Lit un bloc Tree ou Command_line et rend le dictionnaire { partition: data }
correspondant. 'data est la ligne suivant le ':'. On a la garantie que les
noms de partition sont syntaxiquement corrects et uniques (casse insensible).
Génère une exception SyntaxError si erreur, RedundantNameError si une partition
est citée deux fois.
"""
def read_Tree(sec: str,lst: LignesType) -> Dict[str,str]:
    output={}
    dejavu: Set[str] =set()
    for num,lg in lst:
        meth,lg=split_2points(sec,num,lg,None)
        meth=is_partition_name(sec,num,meth)
        ctrl_redond(sec,num,meth,dejavu,("spartition","spartition"))
        output[meth]=lg
    return output

read_Command_line=read_Tree

# -----------------------------------------------------------
# Chargement du fichier Spart.

import enum

"""
Chaque constante dispose des attributs suivants :
    .value      Le titre de la section dans le fichier Spart.
    .oblig      True si la section est obligatoire, False sinon.
"""
class Sections(enum.Enum):
    def __init__(self,val,oblig=False):
        self._value_=val
        self.oblig=oblig

    Project_name=("Project_name",True)
    Date=("Date",True)
    N_spartitions=("N_spartitions",True)
    N_individuals=("N_individuals",True)
    N_subsets=("N_subsets",True)
    Assignment=("Individual_assignment",True)
    Ind_score="Individual_score"
    Spart_score_type="Spartition_score_type"
    Subset_score_type="Subset_score_type"
    Ind_score_type="Individual_score_type"
    Tree="Tree"
    Command="Command_line"

"""
Reader_spart(fich)

L'instance dispose des attributs et méthodes suivants, en plus de ceux hérités
de Source :
    .type       "spart".
    .titre      Le titre extrait du champ "Project_name".
    .date       La date extraite du champ "Date" (datetime).
    .echantillons
                Liste des Echantillon trouvés dans les Methode de l'instance.
                Les Methode ne contiennent pas forcément tous les Echantillon.
    .methodes   Liste des Methode.
    .load()     Charge le fichier (au 1er appel) et rend la liste de Methode
                constituant le fichier.

Les Methode portées par l'instance disposent, en plus des attributs standard,
des attributs suivants :
    .score      Score de la Methode, ou None (extraite du champ
                "N_spartitions").
    .Subset_score
                Liste des scores des espèces (extraite du champ "N_subsets").
                Chaque élément est le score (float) ou None. None si aucune
                espèce n'a de score.
    .Individual_score
                Dictionnaire Echantillon -> score (float). Ne comprend que les
                Echantillon pour lesquels un score est défini. None si aucun
                échantillon n'a de score.
                Noter que les échantillons non listés dans Individual_score ont
                un score à None, et que les échantillons listés dans
                Individual_score mais absents de la méthode sont ignorés.
    .Spartition_score_type
    .Subset_score_type
    .Individual_score_type
                Nom du type, ou None.
    .Tree       L'arbre sous forme textuelle (str), ou None.
    .Command_line
                None si non définie.
"""
class Reader_spart(Source):
    type="spart"

    def __init__(self,fich: str):
        self.fich=fich

    def load(self) -> List[Methode]:
        if not hasattr(self,"methodes"):
            blocs: Dict[Union[str,Sections],Any] ={}
            msg_miss=get_text("Bloc '%s' manquant","Missing '%s' block")
            try:
                with open(self.fich) as f:
                    num: Optional[int] =0
                    vu=False
                    while True:
                        assert num is not None
                        num,titre,lst=read_bloc(f,num)
                        if lst is None: # fin ou begin/end
                            if vu:
                                if titre is None: # fin
                                    raise SyntaxError(msg_miss%"end")
                                if titre=="begin":
                                    raise SyntaxError(msgError(titre,num,
                                                ("Bloc 'begin spart' mal placé",
                                                 "Misplaced 'begin spart' block")))
                                break # "end" rencontré.
                            if titre is None: # fin
                                raise SyntaxError(msg_miss%"begin spart")
                            if titre=="begin": vu=True
                        else:
                            assert titre is not None
                            if vu:
                                blocs[titre.capitalize()]=lst
                # A partir d'ici, 'blocs contient tous les blocs lus dans le
                # fichier :
                #   cle = le titre du bloc (capitalisé)
                #   valeur = la liste des lignes, sous la forme de couples
                #       (num, lg).

                for sec in Sections:
                    if sec.value in blocs:
                        blocs[sec]=globals()["read_"+sec.value] \
                                                (sec.value,blocs[sec.value])
                    elif sec.oblig:
                        raise SyntaxError(msg_miss%sec.value)

                # A partir d'ici, 'blocs contient (en plus) les blocs lus et
                # pour lesquels une fonction de traitement read_XXX() est
                # définie :
                #   cle = la constante Sections.XXX
                #   valeur = le format dépend de la section :
                #
                #   Project_name    Le titre (str)
                #   Date            Le datetime
                #   N_spartitions   Liste de couples (nom, score)
                #   N_individuals   Liste des nombres d'échantillons
                #   N_subsets       Liste de tuple, chaque tuple donnant les
                #                   scores (ou None) de chaque espèce
                #   Individual_assignment
                #                   Un couple (nb_spart, liste), où chaque
                #                   élément de 'liste est un couple (nom,
                #                   liste_rangs)
                #   Individual_score
                #                   Un couple (nb_spart, liste), où chaque
                #                   élément de 'liste est un couple (nom,
                #                   liste_scores)
                #   Spartition_score_type
                #   Subset_score_type
                #   Individual_score_type
                #                   Liste des types (ou None)
                #   Tree            Dictionnaire { nom_spart, ligne }
                #   Command         Dictionnaire { nom_spart, ligne }

                nbpart=len(blocs[Sections.N_spartitions])
                ko: Optional[Sections]
                for sec in (Sections.N_individuals,Sections.N_subsets,
                           Sections.Spart_score_type,Sections.Subset_score_type,
                           Sections.Ind_score_type):
                    if sec in blocs and len(blocs[sec])!=nbpart:
                        ko=sec
                        break
                else:
                    for sec in (Sections.Assignment,Sections.Ind_score):
                        if sec in blocs:
                            nb,data=blocs[sec]
                            if nb!=nbpart:
                                ko=sec
                                break
                            blocs[sec]=data
                            # On supprime le nombre de spartitions ('nb), qui
                            # ne sert plus, pour simplifier la suite.
                    else:
                        ko=None
                if ko:
                    raise SyntaxError(
                        get_text("Nombre de spartitions incohérent entre "
                                 "les blocs %s et %s",
                                 "Inconsistent number of spartitions "
                                 "between the blocks %s and %s")%
                                  (Sections.N_spartitions.value,
                                   ko.value))

                # A partir d'ici, pour les sections Individual_assignment et
                # Individual_score, la valeur de blocs[sec] est la simple liste
                # des couples (nom, liste)

                self.methodes=[]
                self.echantillons=[Echantillon(e)
                                   for e,_ in blocs[Sections.Assignment]]

                # La boucle ci-après traite chaque méthode une après l'autre.
                #
                for rang,((nom,score),subset) in \
                                    enumerate(zip(blocs[Sections.N_spartitions],
                                                  blocs[Sections.N_subsets])):
                    # 'rang est le rang de la méthode dans toutes les listes
                    # du fichier Spart, à compter de 0.
                    # 'nom est le nom de la méthode.
                    # 'score est son score (N_spartitions).
                    # 'subset est la liste des scores des espèces (N_subsets).

                    le=[(e,ass[rang])
                        for e,(_,ass) in zip(self.echantillons,
                                             blocs[Sections.Assignment])
                        if ass[rang] is not None]
                    # 'le est la liste des couples (a,b) où 'a est le
                    # Echantillon et 'b le code-espèce ; elle ne comprend que
                    # les échantillons pour lesquels le code-espèce est !="?".

                    a,b=len(le),blocs[Sections.N_individuals][rang]
                    if a!=b:
                        raise ValueError(
                                get_text("Méthode %s : nombre d'échantillons (%d) "
                                         "incohérent avec %s (%d)",
                                         "Method %s: number of samples (%d) "
                                         "inconsistent with %s (%d)")%
                                (nom,a,Sections.N_individuals.value,b))
                    esp=list(map(itemgetter(1),le))
                    # 'esp est la liste des codes-espèces, parallèle à
                    # self.echantillons. set(esp) est le set des codes-espèces
                    # différents.

                    a,b=len(set(esp)),len(subset)
                    if a!=b:
                        raise ValueError(
                                get_text("Méthode %s : nombre d'espèces (%d) "
                                         "incohérent avec %s (%d)",
                                         "Method %s: number of species (%d) "
                                         "inconsistent with %s (%d)")%
                                (nom,a,Sections.N_subsets.value,b))
                        
                    m=Methode(nom,list(map(itemgetter(0),le)),esp,self)
                    # Le nombre d'échantillons est forcément >=1 car cela a été
                    # testé dans read_N_individuals().
                    m.score=score # type: ignore
                    def notallnone(lst):
                        return any(map(lambda e: e is not None,lst))

                    m.Subset_score=subset if notallnone(subset) else None # type: ignore

                    for sec in (Sections.Spart_score_type,
                               Sections.Subset_score_type,
                               Sections.Ind_score_type):
                        setattr(m,sec.value,
                                blocs[sec][rang] if sec in blocs else None)
                    for sec in (Sections.Tree,Sections.Command):
                        setattr(m,sec.value,
                                blocs[sec].get(nom) if sec in blocs else None)

                    m.Individual_score=None # type: ignore
                    if Sections.Ind_score in blocs:
                        d=dict((e,s[rang])
                               for (e,s) in blocs[Sections.Ind_score])
                        # d : nom_ech -> score (ou None si "?")
                        d=dict((ech,d.get(ech.nom)) for ech in m)
                        # d : Echantillon -> score (ou None si "?" ou si non
                        # fourni dans Individual_score pour cet échantillon
                        d=dict((ech,v) for ech,v in d.items() if v is not None)
                        # d : Echantillon -> score, uniquement si score!=None
                        if d:
                            m.Individual_score=d # type: ignore

                    self.methodes.append(m)
                self.titre=blocs[Sections.Project_name]
                self.date=blocs[Sections.Date]
            except Exception as e:
                raise type(e)(get_text("Ne peut charger le fichier Spart %s",
                                       "Cannot load the Spart file %s")%
                              self.fich)
        return self.methodes

"""
Produit le fichier 'fich au format Spart, à partir de l'ensemble des méthodes
regroupées dans l'Espace 'espace. 'titre est le titre du fichier (section
Project_name). 'fich peut être un objet file-like déjà ouvert.
Génère une exception si ne peut ouvrir le fichier, ou si un échantillon a un
nom non conforme avec la syntaxe Spart.
"""
def Writer_spart(fich: Union[TextIO,str],titre: str,espace: Espace):
    # On travaille entièrement sur les pMethode du Espace, qui prend donc en
    # compte les éventuels renommages et/ou suppressions d'échantillons, ansi
    # que les renommages de noms de méthodes.
    # Pour travailler entièrement sur les Methode réelles, il aurait fallu
    # faire :
    # espace=[m.meth for m in espace]

    """
    Rend la liste des valeurs de l'attribut 'attr pour toutes les méthodes de
    'espace. Si l'attribut n'existe pas ou vaut None, la valeur est None dans
    la liste si 'interog vaut False, "?" si 'interog vaut True.
    Si None (ou "?") pour toutes les méthodes, rend None au lieu de la liste.
    """
    def getlstval(attr,interog=True):
        lst=[getattr(m,attr,None) for m in espace]
        nb=lst.count(None)
        return None if nb==len(lst) \
               else [("?" if v is None else v) for v in lst] if nb and interog \
               else lst

    for pm in espace:
        for pech in pm:
            is_sample_name(get_text("Méthode %s","Method %s")%pm.nom,None,
                           pech.nom)
    if isinstance(fich,str):
        cm=open(fich,"w")
    else:
        from contextlib import nullcontext
        cm=cast(TextIO,nullcontext(fich))
    with cm as f:
        f.write("begin spart;\n")
        f.write("\n%s = %s;\n"%(Sections.Project_name.value,titre))
        f.write("\n%s = %s;\n"%(Sections.Date.value,
                                datetime.datetime.now().
                                                isoformat(timespec="seconds")))

        # N_spartitions
        f.write("\n%s = %d: "%(Sections.N_spartitions.value,len(espace)))
        lstsc=getlstval("score")
        if lstsc:
            f.write(" / ".join("%s, %s"%(m.nom,str(s))
                               for m,s in zip(espace,lstsc)))
        else:
            f.write(" / ".join(m.nom for m in espace))
        f.write("\n;\n")

        # N_individuals
        f.write("\n%s = %s\n;\n"%(Sections.N_individuals.value,
                              " / ".join(str(len(m)) for m in espace)))

        # N_subsets
        f.write("\n%s = "%Sections.N_subsets.value) # type: ignore
        lstsub=getlstval("Subset_score",False)
        lst=[]
        for i,pm in enumerate(espace):
            nb=len(pm.especes)
            s=str(nb)
            if lstsub:
                lst_scores=lstsub[i]
                if lst_scores:
                    lst2=[("?" if sc is None else str(sc))
                          for sc in lst_scores]
                else:
                    lst2=["?"]*nb
                s+=":"+",".join(lst2)
            lst.append(s)
        f.write(" / ".join(lst))
        f.write("\n;\n")

        # Individual_assignment
        #
        # Dans le fichier Spart, les codes espèces sont obligatoirement
        # numériques. Ci-dessous, on construit un espace parallèle 'espace2
        # comme suit, constitué de dictionnaire pEchantillon -> code espèce :
        # - pour les méthodes dont tous les codes espèces sont numériques,
        #   la pMethode est simplement insérée dans 'espace2.
        # - pour les méthodes dont au moins 1 code espèce n'est pas numérique,
        #   on construit d'abord un dictionnaire code_original -> code_numérique
        #   ('on ci-dessous), puis on réaffecte grâce à lui le code espèce de
        #   tous les échantillons : on construit un nouveau dictionnaire
        #   pEchantillon -> code_espèce_numérique. C'est celui-ci qui est
        #   inséré dans 'espace2 à la place de la pMethode.
        espace2=[]
        for pm in espace:
            cdesp=set()
            vu=False
            for ech,sp in pm.items():
                cdesp.add(sp)
                if not isinstance(sp,int): vu=True
            if vu: # Au moins 1 code espèce non numérique.
                on=dict(zip(sorted(cdesp),range(1,len(cdesp)+1)))
                espace2.append(dict((ech,on[sp]) for ech,sp in pm.items()))
            else:
                espace2.append(pm)
        f.write("\n%s =\n"%Sections.Assignment.value) # type: ignore
        for ech in espace.echantillons:
            f.write("%s: "%ech.nom)
            lst=[]
            for pm,vm in zip(espace,espace2):
                if pm.all[ech] is None:
                    lst.append("?")
                else:
                    lst.append(str(vm[ech]))
            f.write(" / ".join(lst))
            f.write("\n")
        f.write(";\n")

        # Individual_score
        lstsc=getlstval("Individual_score",False)
        if lstsc is not None:
            f.write("\n%s =\n"%Sections.Ind_score.value)
            for ech in espace.echantillons:
                lst=[]
                vu=False
                for pm,scores in zip(espace,lstsc):
                    e=pm.all[ech]
                    val="?"
                    if e is not None and scores and e in scores:
                        val=str(scores[e])
                        vu=True
                    lst.append(val)
                if vu:
                    f.write("%s: "%ech.nom)
                    f.write(" / ".join(lst))
                    f.write("\n")
            f.write(";\n")

        # XXX_score_type, Tree, Command_line
        for sec in (Sections.Spart_score_type,Sections.Subset_score_type,
                    Sections.Ind_score_type,Sections.Tree,
                    Sections.Command):
            lst=getlstval(sec.value)
            if lst is not None:
                f.write("\n%s = "%sec.value)
                f.write(" / ".join(lst))
                f.write(";\n")

        f.write("\nend;\n")
