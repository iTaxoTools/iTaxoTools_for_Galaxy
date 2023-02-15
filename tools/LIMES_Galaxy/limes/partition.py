

"""
A partir d'un objet Espace (voir module limes), calcule les partitions qu'il
contient et les affiche dans un mini-tableur canvastableur.STableur.

La fonction de base pour calculer les partitions est limes.communes().
"""

from tkinter import *
from tkinter.ttk import *

try:
    from pydlib.canvastableur import STableur,COLOR_FOND
except ImportError:
    try:
        from .canvastableur import STableur,COLOR_FOND
    except ImportError:
        from canvastableur import STableur,COLOR_FOND

from .core import NOM

"""
Rend le numéro 'num (>=0) exprimé sous la forme alpha : 0=A, 1=B, 26=BA...
Si 'nbcar est !=None, la valeur est complétée par des A à gauche de façon à
occuper 'nbcar caractères.
"""
def mkespname(num,nbcar):
    txt=""
    while True:
        txt=chr(ord('A')+num%26)+txt
        num=num//26
        if num==0: break
    if nbcar is None: return txt
    return 'A'*(nbcar-len(txt))+txt

"""
Calcule toutes les espèces définies par les méthodes de la liste 'meth dans
le Espace 'espace. Rend une liste de couples (a,b), où 'a est le nom sous forme
alpha, créé par mkespname(), et 'b l'espèce (set de ses échantillons).
"""
def named_especes(espace,meths):
    comm=espace.communes(meths)
    if not comm: return []
    nbcar=len(mkespname(len(comm)-1,None))
    return [(mkespname(i,nbcar),esp) for i,esp in enumerate(comm)]

couleurs=(
"#ffd700",
"#79cdcd",
"#f4a460",
"#ffc0cb",
"#caff70",
"#e066ff",
"#ffff00",
"#cdb79e",
"#00bfff",
"#ff6347",
)

from operator import itemgetter

itemgetter1=itemgetter(1)

"""
Partition(espace)

Crée la Toplevel affichant les partitions du Espace 'espace.

L'instance disposes des attributs suivants :
    .espace     Le Espace passé en argument.

Méthodes de classe :
    run()
    close()
"""
class Partition(Toplevel):

    def __init__(self,espace):
        from tkinter import font
        super().__init__()
        # L'ordre vertical d'affichage est déterminé par espace.echantillons.
        nbmeth=len(espace)
        nbech=len(espace.echantillons)
        self.__tab=tab=STableur(self,nbmeth+1,nbech,handler=self.__show_especes)
        tab.grid(row=1,column=1,sticky=NSEW)
        tab.settitreH([NOM(m) for m in espace]+["Species"])
        tab.settitreG(espace.echantillons)
        lab=Label(tab,text="select ->",foreground="#787878",
                  background=COLOR_FOND)
        lab.grid(row=0,column=0,sticky=E,padx=5)
        # On suppose ici que la case NW correspond à la cellule 0x0 de la grille
        # du STableur, ce qui n'est pas du tout spécifié. Ceci en attendant que
        # celui-ci permette d'affecter la cellule logique 0x0, comme dans :
        #   tab.setcellule(0,0,"xxx")
        # Mais la coordonnée logique 0x0 est interdite dans la version
        # actuelle de canvastableur.
        f=font.Font(font=lab.cget('font'))
        f.config(slant='italic',size=8)
        lab.config(font=f)

        for i,m in enumerate(espace,start=1):
            tab.setcolonne(i,[m.get(e,"-") for e in espace.echantillons])
            tab.config_colonne(i,minsize=32,separ=False,anchor=CENTER,padx=2,
                               titre=True)
            tab.config_colonne(i,color="white")
        tab.config_ligne(0,handler=True)
        tab.config_colonne(0,minsize=50,separ=True,anchor=E,padx=10)
        tab.config_colonne(nbmeth+1,minsize=20,anchor=CENTER,titre=True)
        tab.config_colonne(nbmeth+1,color="white")
        tab.config_colonne((nbmeth,nbmeth+1),separ=True,titre=True)
        for i in range(1,nbech):
            tab.config_ligne(i,separ=False,titre=True)
        tab.config_ligne((0,nbech),separ=True,titre=True)
        # On conserve le séparateur après la dernière ligne.
        self.__selection=set()
        # Ensemble des numéros de colonnes sélectionnées.
        self.espace=espace
        self.columnconfigure(1,weight=1)
        self.rowconfigure(1,weight=1)

        tab.config_colonne(nbmeth+1,label=" "*len(mkespname(nbech,None)))
        tab.update_idletasks()
        tab.maj()
        tab.bind("<Map>",self.__fixesize)
        # Il faut mettre le handler sur le Canvas car si on le met sur la
        # Toplevel, celui-ci n'est pas encore dimensionné et on doit faire un
        # update_idletasks(). Noter qu'on suppose que la Scrollbar est dimen-
        # sionnée avant le Canvas...

    def __fixesize(self,ev):
        self.geometry("%dx%d"%(min(self.winfo_width(),1000),
                               min(self.winfo_height(),700)))
##        self.resizable(False,True)
        self.__tab.unbind("<Map>")

    def destroy(self):
        del self.__tab
        super().destroy()

    def __show_especes(self,numcol,numlg):
        if numcol in self.__selection:
            self.__selection.remove(numcol)
            self.__tab.config_cellule(numcol,0,color=COLOR_FOND)
        else:
            self.__selection.add(numcol)
            self.__tab.config_cellule(numcol,0,color="yellow")
        colesp=len(self.espace)+1
        nbcoul=len(couleurs)
        comm=named_especes(self.espace,self.selection())
        dd={}
        for i,(alpha,esp) in enumerate(comm):
            dd.update((ech,(i,alpha)) for ech in esp)
        # 'dd est le dictionnaire {echantillon:espèce}, où 'espèce est repré-
        # senté par un couple (indice >=0, nom alpha). L'indice servira à
        # déterminer la couleur, par modulo.
        for i,ech in enumerate(self.espace.echantillons,start=1):
            esp=dd.get(ech)
            # 'esp=(indice,alpha), ou None si hors espèce.
            self.__tab.config_ligne(i,color="white")
            if esp is None: # L'échantillon n'appartient à aucune espèce.
                self.__tab.setcellule(colesp,i,"")
                ind=-1
            else:
                ind,alpha=esp
                coul=couleurs[ind%nbcoul]
                self.__tab.config_cellule(colesp,i,label=alpha,color=coul)
                for c in self.__selection:
                    self.__tab.config_cellule(c,i,color=coul)
            if i>1:
                self.__tab.config_ligne(i-1,separ=ind!=lastesp,titre=True)
                # On place un séparateur si espèce différente de la ligne
                # précédente.
            lastesp=ind

    """
    Rend la liste des méthodes sélectionnées. La liste est ordonnée dans
    l'ordre du Espace.
    """
    def selection(self):
        return [m for i,m in enumerate(self.espace,start=1)
                if i in self.__selection]

