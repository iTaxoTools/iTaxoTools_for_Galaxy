
from __future__ import annotations

"""
Ensemble des fonctions chargées de la lecture des fichiers mono-méthode :
ABGD, PTP, GYMC.

Leur chargement produit un objet Espace, qui est traité normalement par les
fonctions du module "limes".
"""

import os,re
from .core import (Methode,Echantillon,get_text,Espace,Source,
                   RedundantNameError,EmptyMethodError)

from typing import List,Iterator

class UnknownFormatError(Exception):
    pass

"""
monofmt_ctxt(source)

Gestionnaire de contexte pour la lecture des fichiers mono-format. 'source est
l'instance de Source à charger.

Le contexte rendu à l'ouverture est itérable ; chaque itération donne une ligne
du fichier, non stripée ; les lignes blanches sont éliminées. L'utilisateur doit
renseigner les attributs .echantillons, .codesespeces et .nom. A la sortie du
contexte, .meth contient la Methode créée.

    .echantillons
            Liste des Echantillon de la méthode. La liste est vide à l'ouverture
            du contexte ; l'utilisateur doit y insérer les Echantillon.
    .codesespeces
            Liste des codes espèces associés à l'Echantillon de même indice
            dans .echantillons. La liste est vide à l'ouverture du contexte ;
            l'utilisateur doit y insérer les codes en même temps qu'il
            renseigne .echantillons.
    .nom    Nom de la méthode. Absent à l'ouverture du contexte, doit être
            renseigné par l'utilisateur.
    .numlg  Le numéro de la dernière ligne lue.
    .meth   La Methode créée ; cet attribut est affecté à la sortie du contexte.

L'entrée du contexte génère une exception OSError si le fichier ne peut être
ouvert.

La sortie du contexte procède aux contrôles suivants :
    - Vérifie qu'il n'y a pas d'Echantillon redondants (de même nom).

En cas d'erreur, le bloc exécuté doit générer une exception SyntaxError si le
fichier n'a pas la bonne syntaxe, ValueError si son contenu est invalide,
d'un autre type (OSError notamment) sinon.

Si erreur, la sortie du contexte génère une exception :
    - du même type que celle produite par le bloc exécuté, si celui-ci a
        généré une exception OSError ou ValueError.
    - SyntaxError si celui-ci a généré une exception d'un autre type.
    - RedundantNameError si la Methode produite comporte des Echantillon
        redondants.
    - EmptyMethodError si la Methode comprend zéro échantillons.
Dans tous les cas, le message de l'exception produite comprend le nom du
fichier et son type, l'exception __cause__ donnant le détail (l'exception
produite par le bloc dans le premier cas).
"""
class monofmt_ctxt:
    nom: str

    def __init__(self,source):
        self.source=source

    def __enter__(self) -> monofmt_ctxt:
        self.f=open(self.source.fich)
        self.echantillons: List[Echantillon] =[]
        self.codesespeces: List[int] =[]
        return self

    def __iter__(self) -> Iterator[str]:
        for self.numlg,lg in enumerate(self.f,start=1):
            if lg.strip():
                yield lg.rstrip('\n')
                # La ligne rendue n'est pas stripée, car on peut avoir besoin
                # de tab en tête par exemple (voir PTP). On enlève quand même
                # le \n !

    def __exit__(self,a,exc,c) -> None:
        self.f.close()
        if exc is not None:
            newexc=type(exc) \
                        if isinstance(exc,(ValueError,OSError)) and \
                            not isinstance(exc,UnicodeError) \
                        else SyntaxError
        else:
            if len(self.echantillons)==0:
                exc=EmptyMethodError(
                            get_text("Fichier vide, aucun specimen",
                                     "Empty file, no specimen"))
            elif len(self.echantillons)!=len(set(self.echantillons)):
                exc=RedundantNameError(
                            get_text("Présence de spécimens redondants",
                                     "Redondant specimens"))
            else:
                self.meth=Methode(self.nom,self.echantillons,self.codesespeces,
                                  self.source)
                return None
            newexc=type(exc)
        raise newexc(get_text("Ne peut charger le fichier de format %s:\n%s",
                              "Cannot load the format %s file:\n%s")%
                     (self.source.type,self.source.fich)) from exc

"""
Tous les reader pour fichier mono-méthode ont la même structure, en utilisant
le gestionnaire de contexte 'monofmt_ctxt.

La liste .methodes de l'instance chargée par .load() comprend toujours une
seule Methode.

En cas d'erreur, .load() elle génère une exception :
    - OSError si le fichier ne peut être lu.
    - SyntaxError si le fichier n'a pas la bonne syntaxe.
    - ValueError si le fichier a une syntaxe correcte mais comprend une
        incohérence interne.
Dans les deux derniers cas, .__cause__ donne le détail de l'erreur.
"""

"""
Rend le message (localisé) correspondant à 'msg :
    0   Ligne mal formée.
    1   Ligne non attendue.
Le message inclut le numéro de ligne 'numlg.
"""
def _get_msg(msg: int,numlg: int) -> str:
    if msg==0:
        mmsg=get_text("ligne %d mal formée","line %d malformed")
    elif msg==1:
        mmsg=get_text("ligne %d non attendue","line %d unexpected")
    return mmsg%numlg

"""
Reader pour le fichier 'fich de format ABGD.
Génère une exception OSError, SyntaxError ou ValueError sinon.
"""
class Reader_abgd(Source):
    type="ABGD"

    def __init__(self,fich: str):
        self.fich=fich

    def load(self) -> List[Methode]:
        if not hasattr(self,"methodes"):
            rex1=re.compile(r"\s*Group\s*\[",re.IGNORECASE)
            rex2=re.compile(r"\s*(?P<species>\d+)\s*\]\s*"
                            r"n\s*:\s*(?P<nb>\d+)\s*;\s*id\s*:"
                            r"(?P<specimens>.*)",re.IGNORECASE)
            with monofmt_ctxt(self) as f:
                f.nom=os.path.splitext(os.path.basename(self.fich))[0]
                codesp=set()
                for lg in f:
                    ma=rex1.match(lg)
                    if ma is not None:
                        ma=rex2.fullmatch(lg,ma.end())
                        if ma is None:
                            raise SyntaxError(_get_msg(0,f.numlg))
                        esp=int(ma.group("species"))
                        if esp in codesp:
                            raise ValueError(get_text(
                                "ligne %d : groupe %d redondant",
                                "line %d: redundant group %d")%
                                             (f.numlg,esp))
                        codesp.add(esp)
                        nb=int(ma.group("nb"))
                        lst=ma.group("specimens").split()
                        if len(lst)!=nb:
                            raise ValueError(
                                get_text(
                        "ligne %d : le nombre de spécimens %d ne correspond pas (n:%d)",
                        "line %d: unmatching specimens number %d (n:%d)")%
                                (f.numlg,len(lst),nb))
                        for ech in lst:
                            f.echantillons.append(Echantillon(ech))
                            f.codesespeces.append(esp)
                if not codesp:
                    raise SyntaxError(get_text("Aucune ligne 'Group'",
                                               "No 'Species' Group"))
            self.methodes=[f.meth]
            self.echantillons=f.echantillons
        return self.methodes

"""
Comme Reader_abgd() pour le format PTP.
"""
class Reader_ptp(Source):
    type="PTP"

    def __init__(self,fich: str):
        self.fich=fich

    def load(self) -> List[Methode]:
        if not hasattr(self,"methodes"):
            rex1=re.compile(r"\s*Species\s+(?P<species>\d+)\s*\(",re.IGNORECASE)
            rex2=re.compile(r"[^)]*\)\s*")
            with monofmt_ctxt(self) as f:
                f.nom=os.path.splitext(os.path.basename(self.fich))[0]
                entete=True
                esp=None # True après une ligne "Species".
                codesp=set()
                for lg in f:
                    ma=rex1.match(lg)
                    if ma is None:
                        if not entete:
                            if esp is None or not lg.startswith(("\t"," ")):
                                raise SyntaxError(_get_msg(1,f.numlg))
                            for ech in re.split(r"\s*,\s*",lg.strip()):
                                if not ech:
                                    # Deux ',' contigües, ou ',' en tête ou en queue.
                                    # Supprime aussi le cas d'une liste vide.
                                    raise SyntaxError(_get_msg(0,f.numlg))
                                f.echantillons.append(Echantillon(ech))
                                f.codesespeces.append(esp)
                            esp=None
                    else:
                        if esp is not None:
                            raise SyntaxError(_get_msg(1,f.numlg))
                        entete=False
                        if not rex2.fullmatch(lg,ma.end()):
                            raise SyntaxError(_get_msg(0,f.numlg))
                        else:
                            esp=int(ma.group("species"))
                            if esp in codesp:
                                raise ValueError(get_text(
                                    "ligne %d : espèce %d redondante",
                                    "line %d: redundant species %d")%
                                                 (f.numlg,esp))
                            codesp.add(esp)
                if entete:
                    raise SyntaxError(get_text("Aucune ligne 'Species'",
                                               "No 'Species' line"))
            self.methodes=[f.meth]
            self.echantillons=f.echantillons
        return self.methodes

"""
Comme Reader_abgd() pour le format GMYC.
"""
class Reader_gmyc(Source):
    type="GMYC"

    def __init__(self,fich: str):
        self.fich=fich

    def load(self) -> List[Methode]:
        if not hasattr(self,"methodes"):
            rex1=re.compile(r"\s*##\s*GMYC_spec\s+sample_name\s*",re.IGNORECASE)
            rex2=re.compile(r"\s*##\s*\d+\s+(?P<species>\d+)\s+(?P<specimen>\S.*)")
            with monofmt_ctxt(self) as f:
                f.nom=os.path.splitext(os.path.basename(self.fich))[0]
                entete=True
                for lg in f:
                    if entete:
                        if rex1.fullmatch(lg):
                            entete=False
                    else:
                        ma=rex2.fullmatch(lg)
                        if ma is None:
                            raise SyntaxError(_get_msg(0,f.numlg))
                        f.echantillons.append(Echantillon(ma.group("specimen").strip()))
                        # On est sûr que le nom du spécimen n'est pas vide, et est
                        # stripé des deux côtés. Par contre, il peut contenir des
                        # blancs.
                        f.codesespeces.append(int(ma.group("species")))
                if entete:
                    raise SyntaxError(get_text("Ligne d'en-tête absente",
                                               "No header"))
            self.methodes=[f.meth]
            self.echantillons=f.echantillons
        return self.methodes

all_monofmt=(Reader_gmyc,Reader_ptp,Reader_abgd)

"""
Charge le fichier 'fich, et rend l'instance de Source correspondante.
L'instance a été chargée par .load().

Si 'fich comporte une extension correspondant au nom d'un format connu (casse
insensible), ce format est utilisé. Sinon, la fonction essaie successivement
les différents formats connus (décrits dans 'all_monofmt) ; le format identifié
pourra être retrouvé par l'attribut .type de la Source rendue.

En cas d'erreur, génère une exception :
    - OSError si le fichier ne peut être lu.
    - SyntaxError si le fichier a une extension correspondant à un nom de
        format, et que son contenu n'a pas la syntaxe correspondante.
    - ValueError si le fichier a une syntaxe correcte (pour le format indiqué
        par l'extension, ou pour le format identifié automatiquement) mais
        comprend une incohérence interne. Si le fichier ne comprend aucun
        échantillon, ou des échantillons redondants, l'exception est de type
        EmptyMethodError ou RedundantNameError, qui sont des sous-classes
        de ValueError.
    - UnknownFormatError si l'extension n'indique pas un format précis et si
        le format n'a pu être déterminé automatiquement.
Dans les deux cas SyntaxError et ValueError, .__cause__ donne le détail de
l'erreur.
"""
def Reader_monofmt(fich: str) -> Source:
    ext=os.path.splitext(fich)[1][1:].upper()
    try:
        fn=dict((f.type,f) for f in all_monofmt)[ext]
    except KeyError:
        pass
    else:
        s=fn(fich)
        s.load() # type: ignore
        return s
    for fn in all_monofmt:
        try:
            s=fn(fich)
            s.load() # type: ignore
            return s
        except SyntaxError:
            pass
    raise UnknownFormatError(
                    get_text("Le fichier <%s> n'est pas de l'un des formats %s",
                             "File <%s> is not one of the formats %s")%
                    (fich,", ".join(f.type for f in all_monofmt)))

##"""
##Crée l'Espace incluant toutes les Source mono-Methode de la liste 'monosrc.
##
##Les noms de Echantillon sont d'abord normalisés ; le nom d'origine est conservé
##sous .orig_nom. Ensuite, les Methode sont comparées de façon à établir la
##correspondance entre les Echantillon de toutes les Methode. Seuls sont
##conservés dans chaque Methode les Echantillon qui existent dans toutes les
##Methode. Ainsi :
##    - les Methode qui ont conservé intacte la liste de leurs Echantillon sont
##        intégrées telles quelles dans le Espace rendu ; leur attribut .exclus
##        vaut None.
##    - pour les Methode pour lesquels au moins un Echantillon a été supprimé,
##        c'est une nouvelle instance de Methode qui est intégrée dans le Espace
##        rendu ; leur attribut .exclus donne la liste des Echantillon exclus.
##
##Rend l'Espace produit. Celui-ci porte un attribut .meth_modif, qui est le
##nombre de Methode remaniées (si 0, toutes les Methode de l'Espace sont celles
##apportées par les sources de 'monosrc).
##
##Génère une exception RedondantSpecimenError si la normalisation des noms
##d'Echantillon génère des redondances dans une même Methode, ou EmptyMethodError
##s'il n'y a aucun échantillon commun à toutes les méthodes.
##"""
##def Espace_monofmt(monosrc):
##    meths=[s.methodes[0] for s in monosrc]
##    rex=re.compile(r"\W+")
##    for m in meths:
##        for e in m:
##            e.orig_nom=e.nom
##            e.nom=rex.sub("_",e.nom.lower())
##        if len(m)>len(set(m)):
##            raise RedondantSpecimenError(
##                        get_text("La méthode %s comprend des échantillons "
##                                 "redondants après normalisation",
##                                 "The method %s includes redondant samples"
##                                 "after renormalization")%
##                        m.nom)
##    eset=set(meths[0])
##    for m in meths[1:]:
##        eset.intersection_update(m)
##    if len(eset)==0:
##        raise EmptyMethodError(get_text("Aucun échantillon commun",
##                                        "No common samples"))
##    rep=0
##    newmeths=[]
##    for m in meths:
##        if len(m)>len(eset):
##            rep+=1
##            echantillons=[]
##            exclus=[]
##            codesespeces=[]
##            for ech,esp in m.items():
##                if ech in eset:
##                    echantillons.append(ech)
##                    codesespeces.append(esp)
##                else:
##                    exclus.append(ech)
##            m=Methode(m.nom,echantillons,codesespeces)
##            m.exclus=exclus
##        else:
##            m.exclus=None
##        newmeths.append(m)
##    esp=Espace(newmeths)
##    esp.meth_modif=rep
##    return esp
