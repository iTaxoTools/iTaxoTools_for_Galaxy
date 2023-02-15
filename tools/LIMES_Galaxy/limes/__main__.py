
from __future__ import annotations

usage_fr="""
    % limes -I -m -n 'fich...
    % limes -O -n -c [-s 'sep] 'fmt ['titre] 'fich...
    % limes -C 'fich
    % limes
    % limes -hh

Dans la première forme (-I), charge l'ensemble des fichier 'fich et affiche
les indices calculés sur lensemble des méthodes.

Dans la deuxième forme (-O), charge l'ensemble des fichiers 'fich et produit
le fichier fusionné au format 'fmt. 'fmt a l'une des valeurs suivantes :
    spart   Format Spart. Dans ce cas, le premier argument est le titre qui
            sera stocké dans le bloc Project_name.
    csv     Format CSV.

Dans la troisième forme (-C), contrôle simplement le fichier 'fich, et
affiche un message d'erreur si le fichier est invalide.

Sans argument (quatrième forme), lance l'interface graphique.

Par défaut, si aucune des options -IOC n'est fournie et que des arguments sont
présents, l'option -C est prise en compte.

Dans tous les cas, le type du fichier est identifié par l'extension :
    .spart      Format Spart
    .xls, .xlsx Format Excel
    .csv        Format CSV
    <autre>     Limes tente d'identifier l'un des format mono-partition ABGD,
                GMYC ou PTP.

Dans le cas des fichiers CSV et Excel, l'extension peut être suivie d'un
complément après un ':' :
    - Pour un fichier CSV, il s'agit du séparateur. Exemple : "fichier.csv:;".
        Le séparateur par défaut est la virgule ','.
    - Pour un fichier Excel, il s'agit du nom ou du numéro (à compter de 1) de
        la feuille. Exemple : "fichier.xls:feuille2" ou "fichier.xls:2". Par
        défaut, la feuille numéro 1 est prise en compte.

Options :
    I   Calcule les indices (voir texte).
    O   Fusionne les fichiers et produit un fichier au format 'fmt (voir texte).
    C   Procède simplement au contrôle syntaxique du fichier 'file (voir texte).
    m   Calcule et affiche les match ratio plutôt que les cTax.
    n   Normalise les noms des échantillons avant fusion.
    c   Ne prend en compte que les échantillons communs à toutes les méthodes
        (éventuellement après normalisation si l'option -n est fournie). Option
        forcée implicitement avec -I.
    s   Précise le séparateur 'sep. Seulement si 'fmt vaut "csv". Virgule par
        défaut.
    h   Affiche cette aide. En anglais si répétée.

Auteur : J.Ducasse, février 2019
    modif. :
        mars 2021 : changement complet du format de la ligne de commande
            (options) ; ajout du format Spart.
        avril 2021 : changement interne (utillisation de openpyxl, typing).
            Ajout de l'option -h.
"""

usage_en="""
    % limes -I -m -n 'file...
    % limes -O -n -c [-s 'sep] 'fmt ['title] 'file...
    % limes -C 'file
    % limes
    % limes -hh

In the first form (-I), loads the set of 'file files and displays the indices
calculated on all the methods.

In the second form (-O), loads all the 'file files and produces the merged file
in 'fmt format. 'fmt has one of the following values:
    spart   Spart format. In this case, the first argument 'title is the title
            which will be stored in the Project_name block.
    csv     CSV format.

In the third form (-C), simply checks the 'file file, and displays an error
message if the file is invalid.

Without argument (fourth form), launches the graphical interface.

By default, if none of the -IOC options are provided and arguments are present,
the -C option is taken into account.

In all cases, the file type is identified by the extension:
    .spart      Spart format
    .xls, .xlsx Excel format
    .csv        CSV format
    <other>     Limes attempts to identify one of the single-partition formats
                ABGD, GMYC or PTP.

In the case of CSV and Excel files, the extension can be followed by a
complement after a ':':
    - For a CSV file, this is the separator. Example: "file.csv:;".
        The default separator is the comma ','.
    - For an Excel file, it is the name or the number (starting from 1) of the
        sheet. Example : "file.xls:sheet2" or "file.xls:2". By default, the
        sheet number 1 is taken into account.

Options :
    I   Calculates the indices (see text).
    O   Merges the files and produces a file in 'fmt format (see text).
    C   Simply performs a syntax check of the file 'file (see text).
    m   Calculates and displays match ratios instead of cTax.
    n   Normalizes sample names before merging.
    c   Only takes into account samples common to all methods (possibly after
        normalization if the -n option is provided). Option forced implicitly
        with -I.
    s   Specifies the separator 'sep. Only if 'fmt is 'csv'. Comma by default.
    h   Displays this help. In English if repeated.

Author: J.Ducasse, feb 2019
    modif.:
        march 2021: complete change of the command line format (options); added
            Spart format.
        april 2021: internal change (use of openpyxl, typing). Added -h
            option.
"""

import sys,getopt,os.path
# Noter que les messages du programme sont bilingues, mais que celui-ci
# n'offre aucun moyen de changer la langue par défaut !

from . import core
from .kagedlib import print_error
from .core import get_text,set_langue

from typing import List,Optional,Tuple,TYPE_CHECKING,Union

def usage(arg: Optional[Exception]=None) -> None:
    if isinstance(arg,Exception):
        print_error(arg)
    print("Usage: limes -I -m -n 'file...\n"
          "       limes -O -n -c [-s 'sep] 'fmt ['titre] 'file...\n"
          "       limes -C 'file\n"
          "       limes\n"
          "       limes -hh",
          file=sys.stderr)
    sys.exit(1)

set_langue(1)

"""
Rend le triplet (a,b,c) où 'a est le path complet du fichier, 'b son type
("spart", "csv", "excel" ou ""), et 'c la données extra suivant le ':' (None
si pas de donnée extra ou si type autre que "csv", "excel" ou "excelx").
Génère une exception si une données extra est donnée pour un fichier autre
que csv ou excel.
"""
def arg2type(file: str) -> Tuple[str,str,Optional[str]]:
    dir,fich=os.path.split(file)
    nom,ext=os.path.splitext(fich)
    a,dp,b=ext.partition(':')
    extra: Optional[str]
    if dp:
        ext=a
        extra=b
        fich=nom+ext
    else:
        extra=None
    ext2=ext.lower()
    if ext2==".csv": type="csv"
    elif ext2==".xls": type="excel"
    elif ext2==".xlsx": type="excelx"
    else:
        if dp:
            raise SyntaxError(
                    get_text("':...' valide seulement pour fichiers "
                             "CSV ou Excel",
                             "':...' expected only for CSV or Excel files"))
        if ext2==".spart": type="spart"
        elif ext2==".dat": type="spart"
        else: type=""
    return (os.path.join(dir,fich),type,extra)
""" hack for galaxy. can only process spart files now """
"""
Lit le fichier 'fich et rend la Source correspondant. Celle-ci est chargée.
Le type est déterminé par l'extension, éventuellement complétée de son extra.
Génère une exception si erreur.
"""
def load(fich: str) -> core.Source:
    fich,type,extra=arg2type(fich)
    src: core.Source
    if type=="csv":
        from . import calc
        if extra is None: extra=','
        src=calc.Reader_csv(fich,extra)
    elif type=="spart":
        from . import spart
        src=spart.Reader_spart(fich)
    elif type in ("excel","excelx"):
        from . import calc
        eextra: Union[int,str]
        if extra is None:
            eextra=0
        else:
            try: eextra=int(extra)-1
            except: eextra=extra
        if type=="excel":
            src=calc.Reader_excel(fich,eextra)
        else:
            src=calc.Reader_excelx(fich,eextra)
    else:
        from . import monofmt
        src=monofmt.Reader_monofmt(fich)
    src.load()
    return src

"""
'args est une liste d'arguments donnant les fichiers à charger. Charge tous
les fichiers par load(), et crée et rend l'Espace intégrant toutes leurs
méthodes. Les noms des échantillons sont normalisés si 'norm vaut True. Les
échantillons sont réduits aux communs si 'common vaut True.
Génère une exception si erreur.
"""
def make_espace(args: List[str],norm: bool,common: bool) -> core.Espace:
    meths: List[core.Methode] =[]
    for f in args:
        meths.extend(load(f).methodes)
    return core.Espace(meths,common=common,strict=not norm)

def run_indices(args: List[str],algo: int,norm: bool) -> None:
    espace=make_espace(args,norm,True)
    pr=core.Printer(espace)
    print()
    if pr.pralias():
        print()
    fn=pr.prmratio if algo==core.ALGO_MRATIO else pr.prtable
    fn(True)
    print()
    fn(False)

def run_controle(fich: str) -> None:
    src=load(fich)
    print(get_text("Type %s ; %d partitions ; %d échantillons",
                   "Type %s ; %d partitions ; %d samples")%
                  (src.type,len(src.methodes),len(src.echantillons)))

def run_exporte_spart(args: List[str],titre: str,norm: bool,common: bool) \
                                                                    -> None:
    from . import spart
    espace=make_espace(args,norm,common)
    spart.Writer_spart(sys.stdout,titre,espace)

def run_exporte_csv(args: List[str],norm: bool,common: bool,separ: str) -> None:
    from . import calc
    espace=make_espace(args,norm,common)
    calc.Writer_csv(sys.stdout,espace,separ)

def run_interface():
    try:
        if TYPE_CHECKING:
            pass
            # Les modules dépendant de tkinter ne sont pas type-checkés.
        else:
            from . import wlimes
    except ImportError:
        usage()

##import pdb
##pdb.set_trace()

algo=core.ALGO_CTAX
try:
    opt,arg=getopt.getopt(sys.argv[1:],"IOCmncs:h")
except getopt.GetoptError as e:
    usage(e)
opt_IOC=None
opt_c=opt_m=opt_n=opt_s=False
separ=","
opt_h=0
for o,a in opt:
    if o=="-m":
        algo=core.ALGO_MRATIO
        opt_m=True
    elif o=="-n": opt_n=True
    elif o=="-c": opt_c=True
    elif o=="-h": opt_h+=1
    elif o=="-s":
        if len(a)!=1: usage()
        separ=a
        opt_s=True
    else:
        if opt_IOC and opt_IOC!=o: usage()
        opt_IOC=o

if opt_h>0:
    print(usage_fr if opt_h==1 else usage_en)
    sys.exit(0)

if len(arg)==0:
    if opt: usage()
    run_interface()
else:
    if opt_IOC is None: opt_IOC="-C"
    if opt_m and opt_IOC!="-I" or \
       (opt_n or opt_c) and opt_IOC=="-C" or \
       opt_s and opt_IOC!="-O":
        usage()
    try:
        if opt_IOC=="-C":
            if len(arg)>1: usage()
            run_controle(arg[0])
        elif opt_IOC=="-I":
            run_indices(arg,algo,opt_n)
        else: # "-O"
            fmt=arg[0]
            if fmt=="spart":
                if len(arg)<3 or opt_s: usage()
                run_exporte_spart(arg[2:],arg[1],opt_n,opt_c)
            elif fmt=="csv":
                if len(arg)<2: usage()
                run_exporte_csv(arg[1:],opt_n,opt_c,separ)
            else:
                usage()
    except Exception as e:
        print_error(e,titre=True)
        sys.exit(1)
    else:
        sys.exit(0)
