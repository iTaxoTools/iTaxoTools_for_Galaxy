
from __future__ import annotations

import os
from tkinter import *
from tkinter.ttk import *

from .core import ALGO_CTAX,ALGO_MRATIO,Printer,get_text,Espace
from .wlimes import enregistre,police1,police2,save_file

from typing import Dict

"""
Indices(espace)

Affiche le tableau des indices calculés sur l'Espace 'espace.
"""
class Indices(Toplevel):
    allalgo={ ALGO_CTAX: ("Ctax",".ctax"),
              ALGO_MRATIO: ("Match ratio",".mr") }

    def __init__(self,espace: Espace):
        super().__init__()
        self.columnconfigure(1,weight=1)
        self.rowconfigure(2,weight=1)
        fr=Frame(self)
        fr.grid(row=1,column=1,sticky=EW)
        fr.columnconfigure(3,weight=1)
        self.__choix_techno=IntVar(value=ALGO_CTAX)
        for i,(algo,(nm,_)) in enumerate(self.allalgo.items()):
            Radiobutton(fr,variable=self.__choix_techno,value=algo,text=nm,
                    command=self.__change_radio).grid(row=1,column=i,padx=5)
        choix_collim=BooleanVar(value=False)
        w=Checkbutton(fr,variable=choix_collim)
        w.grid(row=1,column=2,padx=10)
        enregistre(w,"collimateur","collimator")
        w=Button(fr,command=self.__save)
        w.grid(row=1,column=3,padx=2,sticky=E,pady=2)
        enregistre(w,"Enregistrer","Save")

        self.afficheur=aff=Afficheur(self,choix_collim)
        self.afficheur.grid(row=2,column=1,sticky=NSEW,padx=(2,0))
        self.afficheur.affiche(espace,ALGO_CTAX)
        w=Label(self)
        w.grid(row=3,column=1,sticky=W)
        if any(m.exclus for m in espace):
            m1="Attention : %s échantillons ont dû être éliminés"%espace.exclus
            m2="Warning: %s samples had to be discarded"%espace.exclus
        else:
            m1=m2=""
        a,b=len(espace),len(espace.echantillons)
        enregistre(w,"%d méthodes, %d échantillons. %s"%(a,b,m1),
                   "%d methods, %d samples. %s"%(a,b,m2))

    def destroy(self):
        del self.afficheur
        super().destroy()

    # Radio bouton du choix d'algorithme.
    #
    def __change_radio(self) -> None:
        self.afficheur.affiche_algo(self.__choix_techno.get())

    def __save(self) -> None:
        def fn_write(fich):
            with open(fich,"w") as f:
                f.write(txt)

        txt=self.afficheur.gettext()
        if txt and not txt.isspace():
            nmalgo,ext=self.allalgo[self.__choix_techno.get()]
            save_file(self,nmalgo,ext,fn_write)

"""
Sous-classe de Printer spécialisée pour écrire dans l'Afficheur 'aff. 'esp
est le Espace traité.
"""
class affPrinter(Printer):
    def __init__(self,aff: Afficheur,esp: Espace):
        self.aff=aff
        super().__init__(esp)
        self.debligne=None # Pour le 1er appel à index().

    def print(self,msg: str):
        self.aff.text.insert(INSERT,msg)

    def index(self,what: int,arg: Optional[int] =None):
        aff=self.aff
        text=aff.text
        ici=text.index(INSERT)
        if what==10:
            self.meth=arg
            self.debmeth=ici # .debmeth = début cellule méthode .meth
        elif what==11:
            text.tag_add(aff.tag_mcol+str(arg),self.debmeth,ici)
        else:
            deb=self.debligne
            if what==1:
                text.tag_add(aff.tag_titre,deb,ici)
                text.tag_add(aff.tag_ett,deb,ici)
            elif what==3:
                text.tag_add(aff.tag_meth,deb,ici)
                text.tag_add(aff.tag_ett,deb,ici)
            elif what==5:
                text.tag_add(aff.tag_meth,deb,ici)
            elif what==6:
                text.tag_add(aff.tag_claire,deb,ici)
                text.tag_add(aff.tag_mlg+str(arg),deb,ici)
            elif what==7:
                text.tag_add(aff.tag_foncee,deb,ici)
                text.tag_add(aff.tag_mlg+str(arg),deb,ici)
            else: # 0, 1, 4
                self.debligne=ici # .debligne = début de ligne

"""
Afficheur(parent,collim)

L'afficheur est considéré comme chargé lorsque .espace!=None : il est chargé
avec le Espace .espace, créé à partir du ou des fichiers .fich.

Noter que l'Afficheur est conçu pour pouvoir être rechargé avec un nouvel
Espace (passé à affiche(), et non pas à __init__()) mais que, dans la version
actuelle, il n'affiche jamais qu'un seul Espace (affiche() est appelée une
fois à la création du Indices).

L'instance dispose des attributs suivants :
    .espace     Le Espace actuellement chargé, ou None.
    .printer
    .text       Le Text dans lequel est affichée la table.
"""
class Afficheur(Frame):

    tag_titre="titre"
    tag_meth="meth"
    tag_claire="lg0"
    tag_foncee="lg1"
    tag_ett="ett"
    tag_mcol="methcol"  # +numéro de méthode
    tag_mlg="methlg"    # +numéro de méthode
    tag_fixe="fixe"
    couleurs={ "fond":      "#fff8ca",
               "bandeau":   "#bccb61",
               "titre":     "#002110",
               "methode":   "#3c6628",
               "claire":    "#f8ffbd",
               "foncee":    "#add365",  # "#b4aa84"
               "collim":    "red",
               "fixcollim": "blue"
               }
    def_couleurs=couleurs.copy()

##               "claire": "#faebd7",
##               "foncee": "#eed5b7"
##               "claire": "#fff68f",
##               "foncee": "#ffcac4"

##    couleurs={ "fond":      "#f0f8ff",
##               "bandeau":   "#e0e0e0",
##               "titre":     "red",
##               "methode":   "blue",
##               "claire":    "#d1f4ae",
##               "foncee":    "#c1e978"
##               }

    def __init__(self,parent: Frame,collim: Checkbutton):
        super().__init__(parent)
        self.columnconfigure(1,weight=1)
        self.rowconfigure(1,weight=1)
        self.text=text=Text(self,wrap=NONE,state=DISABLED,font=police1,
                            background=self.couleurs["fond"],cursor="arrow")
        text.grid(row=1,column=1,sticky=NSEW)
        self.__vsb=Scrollbar(self,orient=VERTICAL,command=text.yview)
        self.__hsb=Scrollbar(self,orient=HORIZONTAL,command=text.xview)
        text.config(yscrollcommand=self.__vsb.set,xscrollcommand=self.__hsb.set)
        self.__vsb.grid(row=1,column=2,sticky=NS)
        self.__hsb.grid(row=2,column=1,sticky=EW)

        text.bind("<Motion>",self.__survole)
        text.bind("<Button-1>",self.__clic)
        text.bind("<Leave>",self.__leave)
        self.__collimateur=None   # Collimateur mobile
        self.__fix_collim=None    # Collimateur fixe
            # Pour les deux : couple des tag (col,ligne), ou None si pas de
            # collimateur.
        self.printer=None
        self.__set_colors1()
        self.espace=None
        self.__choix_collim=collim

    def destroy(self) -> None:
        del self.text,self.__vsb,self.__hsb,self.printer
        super().destroy()

    # ---------- Collimateur mobile.

    # Si la souris se trouve sur une zone munie des tag du collimateur mobile
    # (de racine tag_mcol et tag_mlg), rend le couple (tcol,tlg) des tags
    # correspondants. Sinon, rend None.
    #
    def __get_collim_tags(self) -> Optional[Tuple[str,str]]:
        tc=self.tag_mcol
        tl=self.tag_mlg
        mc=ml=mcl=None
        for t in self.text.tag_names(CURRENT):
            if t.startswith(tc): mc=t
            elif t.startswith(tl): ml=t
        if mc and ml: mcl=(mc,ml)
        return mcl

    # Rend un itérateur fournissant la liste des tag dynamiques, c-à-d des
    # tags du collimateur mobile, actuellement définis dans l'afficheur. Les
    # tags sont rendus sous la forme de couples (a,b), où 'a est le nom du
    # tag et 'b vaut True pour un tag de colonne, False pour un tag de ligne.
    #
    def __tags_collim(self) -> Iterator[Tuple[str,bool]]:
        for t in self.text.tag_names():
            if t.startswith(self.tag_mcol):
                yield (t,True)
            elif t.startswith(self.tag_mlg):
                yield (t,False)

    # La souris quitte l'afficheur -> on éteint le collimateur mobile.
    #
    def __leave(self,ev: Event) -> None:
        cur=self.__collimateur
        if cur is not None:
            self.text.tag_lower(cur[0])
            self.text.tag_lower(cur[1])
            self.__collimateur=None

    def __survole(self,ev: Event) -> None:
        if self.__choix_collim.get():
            mcl=self.__get_collim_tags()
            cur=self.__collimateur
            text=self.text
            if cur!=mcl:
                if cur is not None:
                    text.tag_lower(cur[0])
                    text.tag_lower(cur[1])
                if mcl is not None:
                    text.tag_raise(mcl[0])
                    text.tag_raise(mcl[1])
                    # Dans la version courante, le collimateur mobile masque
                    # le collimateur fixe. Si on veut que le collimateur fixe
                    # reste affiché quand le mobile passe par dessus, décommen-
                    # ter les 2 lignes suivantes :
##                    if self.__fix_collim:
##                        self.tag_raise(self.tag_fixe)
                self.__collimateur=mcl

    # ---------- Collimateur fixe.

    def __show_fix_collim(self) -> None:
        ftag=self.tag_fixe
        text=self.text
        for tag in self.__fix_collim:
            tag=list(text.tag_ranges(tag))
            while tag:
                s=tag.pop(0)
                e=tag.pop(0)
                text.tag_add(ftag,s,e)
        text.tag_config(ftag,foreground=self.couleurs["fixcollim"],
                        font=police2)
        # Le tag est détruit dans __clic(). Il faut donc lui réaffecter ses
        # propriétés à chaque création ici. L'affectation dans __set_colors1()
        # ne suffit pas.

    def __clic(self,ev: Event) -> None:
        mcl=self.__get_collim_tags()
        if mcl:
            ftag=self.tag_fixe
            self.text.tag_delete(ftag)
            # On détruit systématiquement le collimateur fixe courant...
            if self.__fix_collim==mcl:
                # On clique sur la cellule centrale du collimateur fixe courant
                # -> on laisse le collimateur fixe détruit.
                self.__fix_collim=None
            else:
                # On clique ailleurs -> on reconstruit le collimateur fixe.
                self.__fix_collim=mcl
                self.__show_fix_collim()

    # ---------- Affichage.

    # Vide la fenêtre, puis affiche le résultat du calcul. 'esp est l'instance
    # de Espace représentant l'ensemble des méthodes ; il est aussi sauvegardé
    # dans self.espace. 'fich est le nom du fichier (pour affichage). 'algo
    # est l'algorithme ALGO_*.
    # Crée le Printer self.printer, puis appelle affiche_algo() pour afficher
    # la table résultat.
    #
    def affiche(self,esp: Espace,algo: int) -> None:
        from datetime import datetime
        self.espace=esp
        self.printer=affPrinter(self,esp)
        fich=sorted(set(m.source.fich for m in esp))
        # Attention : si un même fichier est référencé par des path différents
        # (y compris '/' et '\'), il aura autant d'occurrences dans 'fich !
        ff="Source(s) :%s"%(" " if len(fich)==1 else "\n")
        for f in fich:
            ff+=os.path.basename(f)
            try: ff+=format(datetime.fromtimestamp(os.path.getmtime(f)),
                            " - %d/%m/%Y %H:%M:%S")
            except: pass
            ff+="\n"
        ff+="\n"
        self.printer.fichier=ff
        self.__collimateur=self.__fix_collim=None
        self.affiche_algo(algo)

    # Affiche la table correspondant à l'algorithme 'algo (ALGO_*). Le printer
    # doit déjà avoir été créé (self.printer) par affiche() (ne fait rien
    # sinon).
    #
    def affiche_algo(self,algo: int) -> None:
        pr=self.printer
        if pr:
            xpos=self.__hsb.get()
            ypos=self.__vsb.get()
            text=self.text
            text.config(state=NORMAL)
            text.delete("1.0",END)
            for t,_ in self.__tags_collim(): text.tag_delete(t)
            # Cette destruction des tags dynamiques est facultative.

            pr.print(pr.fichier)
            if self.espace.meth_modif:
                pr.print(get_text("Echantillons écartés :\n",
                                  "Discarded samples:\n"))
                x=set()
                for m in self.espace:
                    if m.exclus:
                        x.update(m.exclus)
                for e in x:
                    pr.print("  %s\n"%e.nom)
                pr.nl()
            if pr.pralias(): pr.nl()

            ppr=self.printer.prtable if algo==ALGO_CTAX else \
                                                     self.printer.prmratio
            ppr(True)
            pr.nl()
            ppr(False)

            text.tag_add("all","1.0",END)
            text.tag_lower("all")
            self.__set_colors2()
            if self.__fix_collim:
                self.__show_fix_collim()
            text.config(state=DISABLED)
            self.text.xview_moveto(xpos[0])
            self.text.yview_moveto(ypos[0])

    """
    Rend le texte contenu dans l'afficheur. Rend "" si non chargé.
    """
    def gettext(self) -> str:
        return self.text.get("1.0",END)

    # ---------- Gestion des couleurs et polices.

    """
    Rend le dictionnaire des couleurs courantes.
    """
    def get_colors(self) -> Dict[str,str]:
        return self.couleurs

    # Affecte des propriétés des tags fixes.
    #
    def __set_colors1(self) -> None:
        tag_config=self.text.tag_config
        self.text.config(background=self.couleurs["fond"])
        tag_config("all",foreground="black",font=police1,relief=FLAT)
        tag_config(self.tag_ett,background=self.couleurs["bandeau"])
        tag_config(self.tag_meth,foreground=self.couleurs["methode"],
                   font=police2)
        tag_config(self.tag_titre,foreground=self.couleurs["titre"],
                   font=police2)
        tag_config(self.tag_claire,background=self.couleurs["claire"])
        tag_config(self.tag_foncee,background=self.couleurs["foncee"])
        tag_config(self.tag_fixe,foreground=self.couleurs["fixcollim"])

    # Affecte les propriétés des tags dynamiques. Cette fonction doit être
    # appelée après avoir créé les tags.
    #
    def __set_colors2(self) -> None:
        for t,col in self.__tags_collim():
            self.text.tag_config(t,relief=GROOVE,borderwidth=(2 if col else 4),
                            font=police2)
            self.text.tag_lower(t)

## Autre version :
##    def __set_colors2(self):
##        for t in self.__tags_collim():
##            self.text.tag_config(t,foreground=self.couleurs["collim"],
##                            font=police2)
##            self.text.tag_lower(t)

    """
    Affecte la couleur de 'item (clé dans .couleurs) à la valeur 'coul, et
    réaffiche le contenu de la fenêtre.
    """
    def set_color(self,item: str,coul: str) -> None:
        self.couleurs[item]=coul
        self.__set_colors1()
        self.__set_colors2()

    """
    Réinitialise la table des couleurs aux valeurs par défaut, et réaffiche le
    contenu de la fenêtre.
    """
    def reinit_color(self) -> None:
        self.couleurs.update(self.def_couleurs)
        self.__set_colors1()
        self.__set_colors2()
        
