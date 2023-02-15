
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import (asksaveasfilename,askopenfilenames)
from tkinter.messagebox import showerror,showinfo
import os.path,weakref,sys
from . import core,kagedlib
from .core import get_text

num_version="2.0.1"
date_version="10/04/2021"

OnMac=sys.platform=="darwin"

# -- Messages multilingues ------------

msg_widgets=weakref.WeakKeyDictionary()
# On utilise des weakref car les widget peuvent disparaître lorsqu'ils sont
# dans des Toplevel différentes.

DEF_LANG=1

"""
Affecte le message correspondant à la langue courante, sélectionné dans la
liste 'msgs, pour le widgets 'w.
Si 'w est un widget et 'index vaut None, le message est affecté par :
    w.config(text=msg)
Si 'w est un widget et 'index non None, affecte le label de l'entrée du menu
correspondant à l'index par :
    w.itemconfigure(index,label=msg)
Sinon, 'w est une fonction, qui est appelée avec le message en argument,
charge à elle d'utiliser le message ('index est ignoré).
"""
def set_langue_widget(w,index,msgs):
    m=get_text(*msgs)
    if isinstance(w,Widget):
        if index is None:
            w.config(text=m)
        else:
            w.entryconfigure(index,label=m)
    else:
        w(m)

"""
Enregistre un widget et la liste de ses labels. Ces couples enregistrés seront
utilisés par la suite par change_langue().
'w est soit une instance de Widget, soit une fonction, soit un tuple
(menu,index). Les arguments suivants donnent les messages dans les différentes
langues supportées. Dans la version actuelle : français, anglais.
Le libellé du widget est simultanément affecté en accord avec la langue
courante.
"""
def enregistre(w,*msgs):
    if isinstance(w,tuple):
        w,i=w
    else:
        i=None
    set_langue_widget(w,i,msgs)
    msg_widgets[w]=(i,msgs)

"""
Change la langue courante par celle sélectionnée, et réaffecte le message
correspondant à cette langue pour tous les widgets enregistrés par
enregistre().
"""
def change_langue():
    core.set_langue(select_langue.get())
    for w,(i,msgs) in msg_widgets.items():
        set_langue_widget(w,i,msgs)

# --- Outils ----------

# Crée une pop-up correctement positionnée. Cette classe est destinée à être
# dérivée. La classe dérivée doit définir une méthode .init_popup(), qui sera
# appelée à la création avec les argument *args et **kw. Elle doit définir
# un bouton "Quitter", qui appellera la méthode prédéfinie .quit().
#
class Popup(Frame):
    def __init__(self,*args,**kw):
        tl=Toplevel(fen)
        super().__init__(tl)
        self.grid(row=1,column=1,stick=NSEW)
        tl.rowconfigure(1,weight=1)
        tl.columnconfigure(1,weight=1)
        self.title=tl.title
        self.init_popup(*args,**kw)
        tl.resizable(False,False)
        w,h=fen.winfo_width(),fen.winfo_height()
        x,y=fen.winfo_rootx(),fen.winfo_rooty()
        self.update_idletasks()
        sw,sh=tl.winfo_width(),tl.winfo_height()
        x+=w/2-sw/2
        y+=h/2-sh/2-100
        tl.geometry("+%d+%d"%(x,y))
        tl.transient(fen)
        tl.grab_set()
        tl.wait_window(self)

    def quit(self):
        self.master.destroy()

import sys
if OnMac:
    police1=("Courier","12")
    police2=("Courier","12","bold")
else:
    police1=("Courier","10")
    police2=("Courier","10","bold")

"""
Affiche un message d'erreur dans une popup. Peut être appelée avec 0, 1 ou 2
arguements :
    - sans argument : affiche l'exception courante.
    - avec 1 argument, celui-ci est soit une instance d'exception, soit un
        message (couple (français, anglais).
    - avec 2 arguments, le premier est un message et le 2ième est soit une
        instance d'exception, soit True pour l'exception courant.
Le message et l'exception sont affichés.
"""
def aff_erreur(arg=None,exc=False):
    if os.getenv("LIMES_DEBUG"):
        import traceback
        traceback.print_exc()
    msg=None
    if arg is None:
        exc=True
    elif isinstance(arg,Exception):
        exc=arg
    else:
        msg=arg
    msg=[] if msg is None else [get_text(*msg)]
    if exc:
        if exc is True: exc=sys.exc_info()[1]
        msg.extend(kagedlib.get_exc_msg(exc))
    msg=msg[:1]+[""]+msg[1:]
    showerror("","\n".join(msg))

"""
Affiche une boîte de sélection pour écire un fichier. 'nom est le type de
fichier, 'ext est l'extension par défaut. Une fois les fichier sélectionné, la
fonction 'fn_write est appelée avec le nom du fichier en argument.
Si 'fn_write() génère une exception, affiche son message ; sinon, affiche un
message de confirmation.
Rend True si 'fn_write() n'a pas généré d'erreur, False si elle a généré une
erreur, ou None si l'utilisateur a abandonné la sélection.
"""
def save_file(parent,nom,ext,fn_write):
    fich=asksaveasfilename(parent=parent,
                           defaultextension=ext,
                           filetypes=((nom,ext),
                                      (get_text("Tous","All"),"*")),
                           title=get_text("Fichier %s","%s file")%nom)
    if fich:
        try:
            fn_write(fich)
        except:
            aff_erreur()
            return False
        showinfo(parent=parent,
                 message=
                     get_text("Fichier enregistré : %s","File saved: %s")%fich)
        return True

# -- Chargement des fichiers ----------

def loader_spart(ws):
    from . import spart
    src=spart.Reader_spart(ws.fich)
    src.load()
    return src

def loader_csv(ws):
    from . import calc
    src=calc.Reader_csv(ws.fich,ws.extra.separ)
    src.load()
    return src

def loader_excel(ws):
    from . import calc
    src=calc.Reader_excel(ws.fich,ws.extra.feuille)
    src.load()
    return src

def loader_excelx(ws):
    from . import calc
    src=calc.Reader_excelx(ws.fich,ws.extra.feuille)
    src.load()
    return src

def loader_dflt(ws):
    from . import monofmt
    return monofmt.Reader_monofmt(ws.fich)

loader={
    ".xls":     loader_excel,
    ".xlsx":    loader_excelx,
    ".spart":   loader_spart,
    ".csv":     loader_csv
    }

"""
Crée un menu permettant de sélectionner le séparateur CSV. Le menu est affiché
en appelant (call) l'instance.

L'instance dispose des attributs suivants :
    .separ      Le séparateur sélectionné : ";" ou "," ou "\t" ou " ". Par
                défaut : ",".
    .text       Le nom de celui-ci : "virgule", etc.
    .actif      ACTIVE au départ. Si positionné à DISABLED, le menu est
                toujours affiché mais les items ne peuvent plus être sélec-
                tionnés.
"""
class extra_csv:
    __separ=(
        ("virgule","comma",","),
        ("point-virgule","semicolon",";"),
        ("tab","tab","\t"),
        ("espace","space"," ")
        )

    def __init__(self,fn=None):
        self.__var=IntVar(value=0)
        self.actif=ACTIVE
        self.fn=fn

    @property
    def separ(self):
        return self.__separ[self.__var.get()][2]

    @property
    def text(self):
        return get_text(*self.__separ[self.__var.get()][0:2])

    def __call__(self,ev):
        menu=Menu(ev.widget,tearoff=0)
        for i,(a,b,_) in enumerate(self.__separ):
            label=get_text(a,b)
            menu.add_radiobutton(label=label,variable=self.__var,
                                 value=i,state=self.actif,
                                 command=(lambda l=label: self.fn(l,ev)
                                          if self.fn else None))
        menu.tk_popup(ev.x_root,ev.y_root)

"""
Crée le menu permettant de sélectionner la feuille Excel. Le menu est affiché
en appelant (call) l'instance.

L'instance dispose des attributs suivants :
    .feuille    La feuille sélectionnée, sous forme numérique à compter de 0.
                Par défaut : 0.
    .actif      ACTIVE au départ. Si positionné à DISABLED, le menu est
                toujours affiché mais les items ne peuvent plus être sélec-
                tionnés.
"""
class extra_xls:
    __sheets=None

    def __init__(self,ws,ext):
        self.__fich=ws.fich
        self.__ext=ext
        self.__var=IntVar(value=0)
        self.actif=ACTIVE

    @property
    def feuille(self):
        return self.__var.get()

    def __call__(self,ev):
        if self.__sheets is None:
            try:
                from . import calc
                if self.__ext==".xls":
                    self.__sheets=calc.Reader_excel.get_sheets(self.__fich)
                else:
                    self.__sheets=calc.Reader_excelx.get_sheets(self.__fich)
            except:
##                import traceback
##                traceback.print_exc()
                aff_erreur(("Ne peut lire la liste des feuilles du fichier Excel",
                            "Cannot read the sheets list of the Excel file"))
                return
        menu=Menu(ev.widget,tearoff=0)
        for i,sh in enumerate(self.__sheets):
            menu.add_radiobutton(label=sh,variable=self.__var,value=i,
                                 state=self.actif)
        menu.tk_popup(ev.x_root,ev.y_root)

"""
wSource(parent,row,fich)

Le wSource représente le bloc affichant le fichier 'fich. Il s'étend sur 2
lignes dans le Frame 'parent, sur les rangs 'row et 'row+1.

Il dispose des attributs et méthodes suivants :
    .fich       Le fichier 'fich passé en argument.
    .row        Le rang 'row passé en argument.
    .src        Le Source chargé à partir du fichier. Cet attribut n'est
                positionné qu'après chargement par .load() ; il vaut None avant.
    .extra      Spécifique pour les types CSV et Excel.
"""
class wSource():
    src=None

    def __init__(self,parent,row,fich):
        self.fich=fich
        self.row=row
        ext=os.path.splitext(fich)[1].lower()
        self.__vselbox=BooleanVar(value=True)
        self.__selbox=Checkbutton(parent,variable=self.__vselbox,
                                  command=self.__clic)
        self.__selbox.grid(row=row,column=1,pady=5)

        # Le champ type affiche d'abord l'extension du fichier puis, après le
        # chargement par .load(), le type réel donné par la Source. Pour les
        # type CSV et Excel, il est associé à un objet "extra", spécifique au
        # type, et il est cliquable : le clic fait un call de cet objet.
        # L'attribut .extra est public car utilisé par le loader.
        self.__type=Label(parent,text=ext,foreground="grey")
        self.__type.grid(row=row,column=2,sticky=W,padx=5)
        if ext==".csv":
            self.extra=extra_csv()
        elif ext in (".xls",".xlsx"):
            self.extra=extra_xls(self,ext)
        else:
            self.extra=None
        if self.extra:
            self.__type.bind("<Button-1>",self.extra)
        Label(parent,text=os.path.basename(fich)).\
                                            grid(row=row,column=3,sticky=W)
        self.__nbpart=Label(parent)
        self.__nbpart.grid(row=row,column=4)
        self.__fleche=Label(parent)
        self.__fleche.grid(row=row,column=5)
        self.__fleche.bind("<Button-1>",self.____fleche)
        self.__nbech=Label(parent)
        self.__nbech.grid(row=row,column=6)

        # .__subfr est le Frame listant les pMethode.
        # Chaque pMethode dispose d'un Checkbutton ; .__subvars est la liste
        # des BooleanVar associées à chacun de ceux-ci.
        # .__showed vaut True/False selon que le Frame est affiché ou non.
        self.__subfr=subfr=Frame(parent,borderwidth=2,relief=RIDGE)
        subfr.grid(row=row+1,column=3,columnspan=4,sticky=EW)
        subfr.grid_remove()
        subfr.__showed=False
        self.__subvars=[]

    # Ouvre ou ferme le sous-Frame des méthodes.
    #
    def ____fleche(self,ev):
        subfr=self.__subfr
        if subfr.__showed:
            subfr.grid_remove()
            self.__fleche.config(text="v")
        else:
            subfr.grid()
            self.__fleche.config(text="^")
        subfr.__showed=not subfr.__showed

    """
    Si 'val vaut None, rend l'état True/False du Checkbutton. Sinon, affecte
    celui-ci à la valeur 'val True/False ; de plus, si 'cascad vaut True,
    affecte de même tous les Checkbutton des méthodes.
    """
    def select(self,val=None,cascad=True):
        if val is None:
            return self.__vselbox.get()
        self.__vselbox.set(val)
        if cascad:
            for v in self.__subvars:
                v.set(val)

    # Clic sur le Chechbutton -> sélectionne ou désélectionne tous les
    # Checkbutton des méthodes.
    #
    def __clic(self):
        val=self.__vselbox.get()
        for v in self.__subvars:
            v.set(val)

    # Charge le fichier. Associe la Source ainsi chargée à .src, et crée le
    # Frame .subfr listant les pMethode de la source. Change le champ type
    # en le renseignant avec le vrai type de la source ; affecte sa couleur
    # à noir. Désactive le extra (s'il existe).
    # Si erreur, affiche le message et passe le champ type en rouge.
    # Peut être appelée plusieurs fois : ne fait rien les fois suivantes.
    #
    def load(self):
        if self.src is None:
            try:
                self.src=src=\
                        loader.get(self.__type.cget("text"),loader_dflt)(self)
            except:
                aff_erreur()
                self.__type.config(foreground="red")
            else:
                self.__type.config(text=src.type,foreground="black")
                self.__nbpart.config(text=len(src.methodes))
                self.__nbech.config(text=len(src.echantillons))
                if self.extra:
                    self.extra.actif=DISABLED
                self.__fleche.config(text="v")
                subfr=self.__subfr
                if len(src.methodes)>10:
                    subfr.columnconfigure(1,weight=1)
                    _,_,w,_=subfr.master.grid_bbox(row=0,column=3,col2=6)
                    can=Canvas(subfr,height=200,width=w-10)
                    can.config(highlightcolor=can.cget("background"))
                    # Nécessaire car le clic sur le Checkbutton met le focus
                    # sur le Canvas et affiche une bordure dans la couleur
                    # highlightcolor. Forcée égale à background, elle devient
                    # invisible.
                    can.grid(row=1,column=1,sticky=NSEW)
                    sb=Scrollbar(subfr,orient=VERTICAL,command=can.yview)
                    sb.grid(row=1,column=2,sticky=NS)
                    can.config(yscrollcommand=sb.set)
                    subfr=Frame(can)
                    can.create_window(0,0,window=subfr,anchor=NW)
                else:
                    can=None
                subfr.columnconfigure(3,weight=1)
                subfr.columnconfigure(2,minsize=30)
                for i,m in enumerate(src.methodes):
                    var=BooleanVar(value=True)
                    self.__subvars.append(var)
                    Checkbutton(subfr,variable=var,command=self.__clicsub).\
                                                        grid(row=i,column=1)
                    Label(subfr,text=len(m)).grid(row=i,column=2)
                    t=m.nom
                    if OnMac and can:
                        t+=" "*100 # pour remplir le Canvas par le Frame
                    Label(subfr,text=t).grid(row=i,column=3,sticky=W,padx=(5,0))
                if can:
                    subfr.update_idletasks()
                    wc=can.winfo_width()
                    h=subfr.winfo_height()
                    can.config(scrollregion=(0,0,wc,h))

    def selection(self):
        return [m for v,m in zip(self.__subvars,self.src.methodes) if v.get()] \
                               if self.src else []

    # Clic sur un des Checkbutton du sous-Frame des méthodes. Détermine si
    # toutes les méthodes sont sélectionnées ou déselectionnées, et affecte
    # l'état du Checkbutton général comme suit :
    #   - toutes les méthodes sélectionnées -> True
    #   - toutes les méthodes déselectionnées -> False
    #   - partiellement sélectionnées -> False + apparence "alternate".
    #
    def __clicsub(self):
        cpt=0
        for v in self.__subvars:
            if v.get(): cpt+=1
        val,alt=False,False
        if cpt==len(self.__subvars):
            val=True
        elif cpt:
            alt=True
        self.select(val,False)
        if alt:
            self.__selbox.state(("alternate",))

# -- Ecriture vers fichier Spart ----------

class win_exporte(Popup):
    def init_popup(self,esp):
        self.esp=esp
        self.grid(padx=5,pady=5)

        fr=Frame(self)
        fr.grid(row=1,column=1,sticky=EW)
        self.format=StringVar(value="spart")
        for i,f in enumerate(("spart","csv")):
            Radiobutton(fr,text=f,variable=self.format,value=f).\
                                grid(row=i,column=1,sticky=W,padx=(5,10),pady=5)
        self.titre=Entry(fr,width=50)
        self.titre.grid(row=0,column=2,sticky=EW)

        w=Label(fr)
        self.extra=extra_csv(lambda label,ev: ev.widget.config(text=label))
        w.config(text=self.extra.text)
        w.grid(row=1,column=2,sticky=W)
        w.bind("<Button-1>",self.extra)

        fr=Frame(self)
        fr.grid(row=2,column=1,sticky=EW)
        fr.rowconfigure(1,minsize=50)
        fr.columnconfigure(1,weight=1)
        Button(fr,text=get_text("Enregistrer","Save"),command=self.__save).\
                                    grid(row=1,column=1,sticky=NS)
        Button(fr,text=get_text("Quitter","Quit"),command=self.quit).\
                                    grid(row=1,column=1,sticky=SE)

    def destroy(self):
        del self.titre
        super().destroy()

    def __save(self):

        def fn_write(fich):
            if fmt=="spart":
                from . import spart
                spart.Writer_spart(fich,titre,self.esp)
            else:
                from . import calc
                calc.Writer_csv(fich,self.esp,self.extra.separ)

        fmt=self.format.get()
        if fmt=="spart":
            titre=self.titre.get().strip()
            if not titre:
                aff_erreur(("Titre obligatoire","Title mandatory"))
                return
        if save_file(self,fmt,"."+fmt,fn_write):
            self.quit()

    def __choose_file(self):
        fmt=self.format.get()
        ext="."+fmt
        fich=asksaveasfilename(defaultextension=ext,
                               filetypes=((fmt,ext),
                                          (get_text("Tous","All"),"*")),
                               title=get_text("Fichier %s","%s file")%fmt)
        if fich:
            self.fich.config(text=fich)

def exporte():
    try:
        esp=main.make_espace()
    except:
        aff_erreur()
    else:
        win_exporte(esp)

# -- Images ------------

"""
Les images sont produites par base64.encode() à partir des fichiers GIF.
Noter que la chaîne est scindée en lignes, pour des raisons de présentabilité.
A l'utilisation, les sauts de lignes sont retirés par .replace() : voir la
fonction make_image() ci-dessous.
"""

photoLogo="""
R0lGODlhZAAgAIcAMQQCBESCNJy6NBRCHDyyTAwmFExWHJzOPGyGJNTS1CwyDJSuNFRqHAQSBCRq
LGRmZJyanMzOzLTSPISChBQ2FBQWBDRCFFyyRDSaRLS2tOzq7Cw2DGzGTISaLFx6JBQaBDxSHAQK
BBwiDExeHKTaRLzePGS+RGySLGRyJDx2LHR2dKyqrBQ6HFSePDQ2NJTGPGSCJDy+VKzOPNze3Fxy
JAwaDDSmRMTCxPT29BwaHAwKBBxSJExKTJzWRCwqLIy+PFxuHDRmJIyOjCQyDERCRGzSTCQqDLzm
REyKNKzKPDy6THSOLAwSBGxubKSipGS6RDQ+FHyiNFx+JBweDDReJGTGTAwOBFRSVDxuLKTCNBQq
FJzSPHSKJNza3FRuJLTaPBwyFBQSFDxKFGS2RDSiRLy+vPTy9DQ6FGzOTGR2JBQeDCQiJFxaXLzi
PGTCRHySLHx+fLSytDw+POTm5DSqRMzKzPz+/CxaJDQyNJTCPDxqLJSWlIymLAQGBESGNJy+NCxO
HERaHER+NGRiZGSKLBQiDGxqbLy6vHx6fDw6POTi5Pz6/JSSlHRydHTWTERSFDxCFKTWRMTmRGyK
LAQWDDRqLCQ2FAwWDDy2TNTW1JSyNJyenLTWPISGhFy2RDSeROzu7GzKTAQOBKTeRKyurBQ+HJTK
PDzCVAweDMTGxBweHBxWJExOTCwuLIzCPERGRCQuDEyONKSmpHymNFRWVBw2FBQWFGR6JCQmJHyW
LCwyFFRqJCw2FBQaDAwKDFxuJDy6VAwODJzSRLziRGTCTDSqTAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAAZAAgAAcI/gD7ABhI
sKDBgwgTKlzIsKFDhAIfSpxIsaLFixgzatzIkSCTYB1DNkRFQRRBQILuRAwhJhATghZy5VJA0IUs
WXIGCjFjBo7Inwd3KAGGoQGASmiqoPEz8MQoErMEQinxpQQnEQCYKLJjZw6AB1wX2aEFtCyAT5hs
xGABwJOJMZ7coLJi6sWLLWAALCkhI0mbNADw2BFrx5aTwWIZmf3ZBwMBOkrYun3yxI0aJi/qHoAF
gEubJH6BBObK1RYixHaaLBbZ+DGwAUeLECvC9MOLA7c5G/Hb5k8vAK1I21njKxXXDBFXc2wNuRSA
PoACUAkB4EMezXkBiKABpMJAwaRx/gHwhQePctaO6QBzfrBG5ttGEgYPP1DVmoRrXLQCSbAPLhc+
8LeQLa24gEtyDKnigioJMaeEc30E0YIgl1R33QvCxKcdDTRM8Z1wPgCwCVdOFNRHE12QpsEmDKow
g4p7/IbQFWXgQNoMQtiyECt12GjHAxCl9xoAgBRhQhEpVPfeAXlZIcARkmgiEHhc5aAKaTgwmNUN
wpGmSARdcqVBIgYFE0eYXJnBSkITdNlFkI8pAVsloXjCQSxKmmLKZgAM8UUSMsjgIZV25OCDcOIB
UAZihBFGWqNigXLfQCEYJ5ajg3HFw0GDZEpYJnCqN2edVSABQC9LcqYAJzJIIMMH/qORZiiIADSR
KZq4ikUKQXvcGlajdmRgkC8vCmfGFaHKeVQoY5SaJ4acDcGqq7ASOitp94EZViO4vJKAsYPgcsVW
YYnXiqOL7LGGCo/aAYFBrwi3wn4NCjmqnbWlCoACXwQqgxqxVomLcKqEYaNYjRCkihmZ7vEcAC6E
NRYAndw6CACvABtBGAYZkukcAiY76hhu4GmbnnzCwiqrgwp3bZVrCGdeRIdkqphAfbwoliEA1CxW
GQDw0G4dIQ9kq1gJMMTckHR6EgpTqNrFJy/9BtqyrIeSpsrApLVSUAY2PwxAijsD8K1YiJiNWipF
D9RIpkkv5ODIJQMQwg8k9PBC/oUVJFHCEQIINJ/ALnPNVYgE+WyHYgRlkinPYIrlk+Ni3eBLQuyK
FYHS9i7rNFMAQBFFFBYQtEEub2hIqCpZc7U1rQSBnZjYlKfWc6Y3AMCKWIe0/fBpYtXBeZx0m/rQ
4IW2XqjhdiA+kOyLF0S27XDcynMYiSo04s/Di+r50wMV4oEUnA30CB98lB7w8gQz7/zts0dUO8/n
CrdJIrjgYaBBtshRcdhywwAmIHMvDjBFDXjrwQEsAQAxtKEqX6CJtZSXA/d9DYADmZ9OfNWldw1k
DXMIE5kCSIBiYKKAeGIACfLwgh4QAgBv6JffbgExglGQeV6LXaaEQLvHJY5R32HKYfUWcSl3OeQT
BLAB00JxgTsBgAE9cEUeIvFCBAwDNEdgAABwQRgchEEVXQxDDhqVg4LIwg42ShtB6pApZAkkBGfE
FeIyR5oVPMQBMYgBGYwCBjeEAg2AAEAhXJG3LWxAO1loQxs08RIAtGkRCaPYYCKJCCKqkSCt2Eod
dESQV4DCDqRAUNAy8EnhOGwgYSjDIkBRBzZMZAA7oARBtECFWhBEBB6AwRAIUoERGKCRA7EFJ4M5
TAAIEyG+0JJBwjAphATDB60oTzMJkgOOneea2MymNrfJzW5685sICQgAOw==
"""

photoPython="""
R0lGODlhIAAgAHcAACH5BAEAAMQALAAAAAAgACAAh0NkfkNkf0Rie0RifERjfERjfUVjfD9tkj9t
kz9ulD5vlz5wmD5wmT5xmj1ynD1ynT1ynj1znj1znzt2pjt3pzx0oT10oDx1ojx1ozx1pDx2pTx2
pjt3qDt4qTp5qzt4qjp5rDp5rTp6rTp6rzp7rzl7sDl8sTl8sjl8szh9tTl9tDh+tjh+tzh/uENl
gUNlgkJmg0JmhEJnhkJoh0FoiEFpiUFpikBqjUBrjUFqjEBrjkBsj0BskVh9mkV4oUJ9rTeAuzeB
vD6GwECCuFWCpmiBlW+UsW+WtWyYuk+QxE+SyWqgzWii0f67I/67JP69Jv6+J/68Kv6/KP7AKv7B
K/7CLP7DLf7ELv7EL/7CMf7GMP7HMf7HMv7AO/7DPv7IM/7JNP7KNf7LNv7MN/7LPP7MOP7NOf7N
Ov7OOv7OO/7PO/7QPP7QPf7QPv7RPv7RP/7SP/7KWP7NW/7SQP7TQf7VQ/7VR/7WRP7WRf7XRf7X
Rv7ZSf7aSf7aSv7bS/7cTP7dTv7eT/7fUP7aW/7abP7ecf7gUf7hUv7hU/7iVP7iVf7jVf7jVv7k
V/7lWP7mWf7nWv7oXP7pXf7pXv7qX/7jZv7rYP7sYf7hdZycnLa2tri4uLq6uq7B0v7wgP7vs8HB
wcLCwsTExMbGxsfHx8jIyMnJycvLy8zMzM3Nzc7OztDQ0NHR0dPT09TU1NXV1dbW1tfX19jY2NnZ
2dra2tvb29zc3N3d3d7e3t/f39Ph7dPj79Xh7NXi7tvj6tnk7Njn89nn8v7wzv7xz///wP7y0/7x
1P7x1f7z1P722/733ODg4OHh4eLi4uPj4+Tk5OXl5ebm5ufn5+jo6Onp6erq6uvr6+zs7O3t7e7u
7u/v7+ju8+nu8/756fDw8PHx8fLy8vPz8/T09PX19fb29vf39/j4+Pn5+fr6+vv7+/z8/P39/f7+
/s2gau+Gk++2NAgHXQAAAAABAPX1pAAAAu+2Eu+Gk++2NAgHXQAAAAABAPX1xAAAAu+2Eu+1/fX1
wAj/AIkJHEiwoMGDBs+ZM3eu4Tl0EMl9g6ZKVjOECM0JHFeLGjVbzcJJYzYLlaZszDAmFFiu3MJz
06ZFq3XqFSdm1FKqHIiu5cuH6NKlU5dOnCpo0nLuFIhO4Dlc17AtU6du3Tp26lx5A7Xpmail6ZgK
pWqVndV0sM65CiVtVKqdRIdWvWp2HVVzrdKNs7ZsFjRaKtcJXBcN27Vo2iYyGzdulSrHpohlUhVY
ILuctFYty1Wt2Thx1ryJE3dNYGSM7OpSPTcOnUNzLcmRGxfOWrNYKtkJTLfsWbZo58qFK/eN2a1x
6lKnXhcu7EHBxNCtinWrlrlstshpg+Us2JIhJDpg//BhxJdug+pcK4RdTjbj0euS7Or1IUOEBQd6
nC/o3JytZdI4U5g4iYXDTgu68LKBBAwggMMM+xHUFDHkqALLN6S0Qks4t1DzDTsohEBBBQ0koAMN
L0TIk3ufiRNOOOCYQ5dyqXWyQw0wFEDjfucIJE4tucwCzi3eAKMEECmMIN4DCvBgQwwACMBOIHwM
ksx5GhETzjLNYPONLd8wEcQKJdQHAX45yBCAAFL6gQcchJxXDjjgfPONN95oo806QrBgggcaMIjA
DTO4MIAABrCjxxxokCGnQHhqgx02B54AwgQWlHjiCwSwWUQ3dKgRhhbnkSOQpNlcU8o17KggwohH
bP+zY2rdFLKGGFtQUSqq2Bh2jTXsjMDBBQ5w48kll1gCiSKB7FFHG2VwUcUT540j0DW/VvNKNev8
kAGT7CBrSSSMCNLHHW+Y8YUVUERxnjgCWWNNNdCEQs05SDB4QLiXSNKIIX7kwSgYV0jRRBzn1VZN
NR7FJI02vxCRAA7hTuLIIX/oQUcaYWAxhRNdGJOwQNSkwkotrkRzCzPJpUbJI4gA8smsyg0EjkDS
gGKKKqjUskopophSCjuQJNJsHWyMsUUVKgr0ClLRPAMNNM44s3Iz1bGziLl3uFEGMsNA0TRB00DD
jCz/UTbQOpW4CccZYBQjjBdjL2WZMpjYwTEWWcgLcUzddhNDc2oGBQQAOw==
"""

photoCalculer="""
R0lGODlhPAAnAIcAMRxuLJSmnJzWhFS2NNTa1FyGZNTuzDyGRFy6PJy+pLzWxOzu7Dx6TISahMTK
xIy6lFyWZOz65CR6NLzirKzGrKzanHSifNTqxGy+TKy6tGyKbJTOfPz6/MzmvJS2nOTu5FSWZEx+
VDR+PHyyjCxyNNTi1FSGXOz25HzGZHSWfLTirMzSzPT67MTqvKzepHTGXGySdIzOdKSupKTWjNza
3GS6RKTGrMzazFyebCyCPMTmtNTm3HTCVOz29JyupGyidNzu1ESKVKS+rDyCRCx6NLTOvIyilJzS
hOT25FSCXIy2lDR2PITKbPT+7CR2NJyqnFy2PNTe1FySZDyKTMTWzER+TIyejLzSvLzmtLTKtKze
lHSqfGzCVHSOdJTSfPz+9MzqvKSypOTy3EyCVDSCRIS2jEyOVNTS1LTepHSSdKTalGS+RGSebNzm
3PT29Nzy1Cx+PCRyNJzWjFS2PNTa3FyKZDyGTFy6RJzCpOzy9Dx+RISajFyWbOz67LzitKzKtNTq
zGyedISujHyqhLS6tGyOdNzq5JS6nCx2NHzKZNze3MzezKTCrMTazGy+VDR+RNTi3Oz27MzS1PT6
9IzOfKTWlMTmvHTCXCx6PDR2RITKdPT+9JyqpLzSxKzenJTShPz+/MzqxOTy5EyCXEyOXLTerHSS
fGS+TGSedPT2/Nzy3AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAAPAAnAAcI/gBBCRxI
sOBADgfP+OgSIhOJOBBJZAphyscZhAIxGtzIsWNBB3vGxHFih42SIo1K3PjzgA0ZJ07GNHDgsabN
gzJGwYRjQYHGTX02DXTzBwJMJ0lkuLnJtGAYBhKCDKJQAtQmPxtQYKhRY40jJpUMCGzE6IcdJ3rC
NGV6JgmcH1QIGqgBZQ6CGnfW4EUAZUAMjamy8MGURNJaj0/i4IhidQITRyfEQFlzirJey6cQxAA1
l8kEgVRAIApw2CAHGJgOWZ1RY8CdAZ+5dOWq9xTXU1AsgaIEBcEcDJ4EHoJTSONhNwUk/AGlgy5l
DJpBxYBSuYbt2ne4cDjRtfoAHqFA/hWBU2BB6QUmnFAAVWmO9dl3MIAqNcC27TuVcR8BpWZObcp3
IIAGKFcQkYR5TXFQRxwegHJEfZdZt8YcBoiBwHXVdYWAWDzcRpttA1QACiNOFGBcTaZIEAh/9c12
Sl50qQEKD3fMhteLl4ASyoUu3obbZxZIUAhTMsChRx6WUNdjbQigAMonPOa3BhQzgLLBZO9FeJkY
PeiRAyc20SBCHAqAckmUXeH33h2RdNDiGjVmpsok1y1p3SkDUAJKAgDoQUdNBTjRiUBvQFfnoVBM
MEmPmeXoB4RqqgkiE6IIJEiJoJw4ECFOJPAFFyIiwYOSh66BABOgMMEjZVSmiuYa/kzeEdwkcugA
ihQSEMIRBwygAgoKvcUwySRMtIgfnJdNgsabNczxRh+zRXgKniiIwRwGc0AhxgciVHEiQoSQsUAF
A7DKgyoO+nconpZYuCYXoKAxh313IoBAJaCcoAkU8TW5ZxwZZFpQCAlE4F93d+mGxl30TqkJKC/E
iYAXrko7Bxdi+TFlZZQN4AcHZiRhEA1kuAHloXRVCUhmKE+iBnUTWhLJXXe25gUHLMQwgIQewktB
HAQUZEUZi0rb3RxM9BEJCi1W5jEQLdbAggow76UCKJbgVt2hA4CRyhRWCCxQEo2A0TSMTGIQngDu
UXbqjDUgkIir1iHgyBsOQtFV/m0uTrnZICEQtAADPbCNsppwIlClDgHahsAJcthbQR9xQsHEJGLw
oO6aesF4hyOg/EECgqA4QMqvCPB9bLTNviCGGJcMgC0ab9glhh+TDSCjCgig3V1t9sEZQQlO0ISQ
DD984YiHlDHq9h1oTHKEXShMwsMp0u0cCgc6v2dfnKzjZsACZKiFUApE/y7ltM3Ti4AmJ7TQGhJy
bIbAJSe8wQUUGKyPGWXsYxcHprCHgWhACX2wyx16wy8GBqh3EGwNAvwAu0oAoQOhuBx9+GUvvizQ
gw304GsmwAE7dAEUNFCEKWwQARS48IUwjOELmYACLkRPB0JBAigm4AgU0FCGnUB8IQ86wAEcmEIR
pUmiEgdyhiY60YkEaIMhBCIKMSDhdVe8YqawaMUuvo4FoIgEFitQoSqeQCAfaAMBnvjEJSZRB1Cg
mBIRoik3EkQU/TuFHzxCR7HZsSkxaB4XIvHHQsrlQzXAlyENuYFp7Q0Dk1hkIWXDt1NcQJJ2nIRs
MIQAdGHSjUxon3U+ace5zAYBuiGlG0OBglOgoBRrCQgAOw==
"""

photoMicroicon="""
R0lGODlhQwA8AIcAMdwCDOyCZPTCrORCJPSihORiPPzi1OxyVPSynOySbPzSxPzy7OQuRORSNOxq
fOQSJPSmnOxqROxyhPSelPzq5PS6pPSKlPzOxOyadOyKbOx6XPzazOxWZOQKHPTKvPSqjOxGVOxi
TPSyvORaRORKLPzi5Pz69OxqVOQCHOyCdPTCvPSilOx2ZPS2rOySfOQaLPSunPzu9PSajPze3Oxi
ROx2VPS2nPzWxOx6hPzu5PS+tOyKfOx+bOxeRNwCHOyGbPTGtORGLPSmjPzm3OyWdPz29OQ2RORW
PPSmrOxuTPSepPS+rPSafOx+ZPze1OQOJPzOvPSulOxmTORePORONPzm5Pz+/OxuVOQeNNwCFOyC
bPTCtORCLPSijORiRPzi3OxyXPSypOySdPzSzPzy9ORSPOQWLPSqnOxqTOx2hPzq7PS6rPzO1OyO
dOx6ZPza1OxebOQKJPTOvPSqlPS2vORKNPz6/OQGHOyGdPTGvPSmlOyShOQaNPSupPSehPze5Oxm
ROx+jOQ6TOyOfPSefOx2XPS2pPzWzPzu7PSerOxmVOReRPzm7OxuXAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAAQwA8AAcI/gCtCBxI
sKDBgXYOKlzIsOHBhA4jSpxI8SAZFWf6jIHIsMgCjgvtHKpgY4kTh2zScIBjocRCHT2CyCQBZsbC
Q20KHWgSBmRBCkISMBHDJAGCIgstoACwFMATOgfDBKFy5EiZIySO2DSYhwYgNGgiTHGhcIEfJhgI
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
8pr3vAUJCAA7
"""

# ---------------------------------------
# -- Création de l'interface ------------

fen=Tk()

def make_image(img):
    return PhotoImage(data=img.replace("\n",""),format="GIF")

photoCalculer=make_image(photoCalculer)
photoLogo=make_image(photoLogo)
photoPython=make_image(photoPython)
photoMicroicon=make_image(photoMicroicon)
del make_image

select_langue=IntVar(value=core.set_langue(DEF_LANG))

# -- Menu Aide ------------

class affiche_apropos(Popup):
    def init_popup(self):
        from tkinter import font
        fr=Frame(self)
        fr.grid(row=1,column=1,padx=5,pady=10)
        w=Label(fr,text="Limes\n"+
                    get_text("Un outil automatisé pour la comparaison\n"
                             "des taxonomies",
                             "An automated tool for taxonomies\n"
                             "comparison"))
        w.grid(row=1,column=2,padx=(10,0))
        f=font.Font(font=w.cget('font'))
        f.config(weight='bold',size=8)
        w.config(font=f)
        Label(fr,image=photoLogo).grid(row=1,column=1)

        txt="""version %s - %s

%s :

Jacques Ducasse
Aurélien Miralles
Visotheary Ung

----""" %       (num_version,date_version,
                 get_text("Conception et développement",
                          "Conception and development"))
        Label(self,text=txt,justify=CENTER).grid(row=3,column=1,pady=10)
        fr=Frame(self)
        fr.grid(row=4,column=1)
        txt="""%s Python v.%d.%d :
http://www.python.org

%s xlrd %s openpyxl :
https://pypi.python.org/pypi/xlrd
https://pypi.python.org/pypi/openpyxl""" % \
                (get_text("développé en","developed with"),
                 sys.version_info.major,sys.version_info.minor,
                 get_text("utilise les modules","uses the modules"),
                 get_text("et","and"))
        if getattr(sys,'frozen',False) and hasattr(sys, '_MEIPASS'):
            txt+="""

%s PyInstaller :
https://www.pyinstaller.org""" % \
                get_text("version exécutable faite avec",
                         "executable version built with")
        Label(fr,text=txt,justify=RIGHT).grid(row=1,column=1,padx=(0,5))
        Label(fr,image=photoPython).grid(row=1,column=2,sticky=N)
        Button(self,text=get_text("Fermer","Quit"),command=self.quit).\
                    grid(row=5,column=1,pady=(15,5))

aide_fr="""
Les données sont fournies sous la forme d'un tableau échantillons/méthodes : chaque ligne
correspond à un échantillon et chaque colonne à une méthode. Dans une même colonne, tous
les échantillons considérés comme appartenant à une même espèce portent le même numéro.
La valeur absolue des numéros n'a pas d'importance ; de même il n'y a pas de lien entre
les numéros portés par un même échantillon pour les différentes méthodes.

Le tableau peut être donné dans un fichier de format CSV (.csv), avec la virgule comme
séparateur, ou de format Excel (.xls ou .xlsx). Dans ce dernier cas, la page contenant le
tableau doit être précisée (en décochant "feuille 1") ; par défaut, le tableau est
recherché dans la première page.

Le tableau est localisé dans la feuille de la façon suivante :

La première ligne non vide dans la page constitue la ligne de titre des méthodes, chaque
cellule donnant le nom d'une méthode. La première colonne non vide, à gauche de la
première colonne de méthode, constitue la colonne de titre des échantillons, chaque
cellule donnant le nom d'un échantillon. Les colonnes plus à gauche sont ignorées.

Il existe une autre méthode pour localiser le tableau :

Si une cellule de la page comprend le mot "LIMES", cette cellule définit l'intersection de
la ligne de titre des noms de méthodes et de la colonne de titre des noms d'échantillons.
Toutes les lignes au-dessus et toutes les colonnes à gauche sont ignorées. Ceci permet
plus de souplesse pour intégrer d'autres informations dans la page.

Dans tous les cas :

- Les colonnes dont la cellule de titre est vide sont ignorées ; de même les lignes dont
la cellule de titre est vide. Ceci permet de laisser des colonnes vides, ou même d'insérer
des commentaires en face d'une cellule.
- Si les titres de plusieurs colonnes sont identiques, un suffixe numérique leur est
ajouté pour les distinguer. De même pour les titres des lignes.
"""

aide_en="""
The data are provided through a samples/methods table: there is one line for each sample
and one column for each method. Inside a given column, all the samples wich are viewed
to belong to the same species have the same number. The actual value of the numbers
doesn't matter; in the same way, there is no relation between the numbers of a given
sample through the several methods.

The table can be provided in a CSV formated file (.csv), with the comma as delimiter, or
in a Excel file (.xls or .xlsx). In this case, the sheet includind the table has to be
indicated (by unchecking the "sheet 1" box); the default is to look for the table in the
first sheet.

The table is located inside the sheet as following:

The first non empty line in the sheet is the title line of the methods, each cell giving
the name of a method. Then, the first non empty column, on the left of the first method
column, is the title column of the samples, each cell giving the name of a sample. The
columns more on the left are ignored.

There is another method to locate the table in the sheet:

If a cell anywhere in the sheet contains the word "LIMES", this cell defines the
intersection between the title line of the methods and the title column of the samples.
All the lines above and all the columns on the left are ignored. This method allows more
flexibility to include other data in the sheet.

In all cases:

- If the title cell of a column is empty, all the column is ignored; the same for the
lines where the title cell is empty. This allows to let empty columns and lines, and even
to insert comments around the cells containing the numbers.
- If the titles of several columns are the same, they are renamed with a numeric suffix.
The same for the titles of the lines.
"""
                                         
class affiche_aide(Popup):
    def init_popup(self):
        Label(self,text=get_text(aide_fr,aide_en)).\
                    grid(row=1,column=1,padx=5,pady=5)
        Button(self,text=get_text("Fermer","Quit"),command=self.quit).\
                    grid(row=5,column=1,pady=(15,5))

# -- Barre de menus ------------

menubar=Menu(fen,tearoff=0)
fen.configure(menu=menubar)
fen.columnconfigure(1,weight=1)

menubar_index=0

# Menu [Langue]
#
menu=Menu(menubar,tearoff=0)
menubar.add_cascade(menu=menu)
enregistre((menubar,menubar_index),"Langue","Language")
menu.add_radiobutton(label="English",variable=select_langue,value=1,
                     command=change_langue)
menu.add_radiobutton(label="Français",variable=select_langue,value=0,
                     command=change_langue)
menubar_index+=1

# Menu [Aide]
#
menu=Menu(menubar,tearoff=0)
menubar.add_cascade(menu=menu)
enregistre((menubar,menubar_index),"Aide","Help")
##menu.add_command(command=affiche_aide)
##enregistre((menu,0),"Aide","Help")
menu.add_command(command=affiche_apropos)
enregistre((menu,1),"A propos","About")

del menubar_index

# -- Tableau principal ------------

"""
Le Frame principal affichant la liste des fichiers.

Il dispose des attributs et méthodes suivants :
    .src        Liste des wSource.
"""
class Main(Frame):
    def __init__(self,parent):
        Frame.__init__(self,parent)
        self.src=[]
        self.__var=BooleanVar(value=True)
        Checkbutton(self,command=self.__clic,variable=self.__var).\
                                                    grid(row=0,column=1,pady=5)
        Label(self,text="Type").grid(row=0,column=2)
        w=Label(self)
        w.grid(row=0,column=4)
        enregistre(w,"Méthodes","Methods")
        w=Label(self)
        w.grid(row=0,column=6)
        enregistre(w,"Echant.","Samples")
        Separator(self,orient=HORIZONTAL).\
                                grid(row=1,column=1,columnspan=6,sticky=EW)
        self.columnconfigure(3,weight=1)
        self.__nextrow=1

    # Clic sur le Checkbutton -> transmet à tous les wSource.
    #
    def __clic(self):
        val=self.__var.get()
        for ws in self.src:
            ws.select(val)

    # Rend la liste des wSource sélectionnés.
    #
    def selection(self):
        return [s for s in self.src if s.select()]

    def chercher_sources(self):
        lst=askopenfilenames(title=get_text("Fichier source","Source file"))
        for f in lst:
            self.src.append(wSource(self,self.__nextrow*2,f))
            self.__nextrow+=1

    def effacer_sources(self):
        for s in self.selection():
            for w in self.grid_slaves(row=s.row)+self.grid_slaves(row=s.row+1):
                w.destroy()
            self.src.remove(s)
        if not self.src:
            self.__nextrow=1

    def charger_sources(self):
        for s in self.selection():
            s.load()

    """
    Crée et rend un Espace avec toutes les méthodes sélectionnées. Les options
    'kw sont transmises à Espace.
    Génère une exception ValueError si aucun méthode n'est sélectionnée, ou
    transmet les exception générées par la création de l'Espace.
    """
    def make_espace(self,**kw):
        lst=[]
        opt={ "common": not choix_tous_ech.get(),
              "strict": choix_strict.get() }
        opt.update(kw)
        for s in self.src:
            lst.extend(s.selection())
        if not lst:
            raise ValueError(get_text("Aucune méthode sélectionnée",
                                      "No selected methods"))
        return core.Espace(lst,**opt)

if OnMac:
    # Pour éviter la marge blanche
    fen2=Frame(fen)
    fen2.grid()
    main=Main(fen2)
else:
    main=Main(fen)
main.grid(row=2,column=1,padx=5,pady=5,sticky=NSEW)

# -- Tableau de contrôle ------------

if OnMac:
    ctrlpanel=Frame(fen2)
else:
    ctrlpanel=Frame(fen)
ctrlpanel.grid(row=1,column=1,pady=5,sticky=EW)
ctrlpanel.columnconfigure(10,weight=1)

# -- cadre 1

fr=Frame(ctrlpanel,borderwidth=2,relief=FLAT)
fr.grid(row=1,column=1,padx=5)

w=Button(fr,command=main.chercher_sources)
w.grid(row=1,column=1,padx=5,pady=2,sticky=EW)
enregistre(w,"Chercher","Browse")

w=Button(fr,command=main.charger_sources)
w.grid(row=2,column=1,padx=5,pady=2,sticky=EW)
enregistre(w,"Charger","Load")

w=Button(fr,command=main.effacer_sources)
w.grid(row=3,column=1,padx=5,pady=2,sticky=EW)
enregistre(w,"Supprimer","Remove")

# -- cadre 2

fr=Frame(ctrlpanel,borderwidth=2,relief=RIDGE)
fr.grid(row=1,column=2,padx=15)

def show_partitions():
    from . import partition
    try:
        esp=main.make_espace()
    except:
        aff_erreur()
    else:
        partition.Partition(esp)

w=Button(fr,command=show_partitions)
w.grid(row=1,column=1,padx=5,pady=2,sticky=EW)
enregistre(w,"Partitions","Partitions")

def show_indices():
    from . import indices
    try:
        esp=main.make_espace(common=True)
    except:
        aff_erreur()
    else:
        indices.Indices(esp)

w=Button(fr,command=show_indices)
w.grid(row=2,column=1,padx=5,pady=2,sticky=EW)
enregistre(w,"Indices","Indices")

w=Button(fr,command=exporte)
w.grid(row=3,column=1,padx=5,pady=2,sticky=EW)
enregistre(w,"Exporte","Export")

choix_tous_ech=BooleanVar(value=True)
choix_strict=BooleanVar(value=True)
w=Checkbutton(fr,variable=choix_tous_ech)
w.grid(row=1,column=2,sticky=W)
enregistre(w,"Tous échant.","All samples")
Checkbutton(fr,variable=choix_strict,text="Strict").\
                                        grid(row=2,column=2,sticky=W)

# Logo.
#
w=Label(ctrlpanel,image=photoLogo)
w.grid(row=1,column=10,sticky=NE,padx=(10,5))
##if sys.platform=="darwin":
##    w.bind("<Control-Button-1>",ChoixCouleurs)
##else:
##    w.bind("<Alt-Button-1>",ChoixCouleurs)

# --- Feu ! ----------

fen.title("Limes v.%s"%num_version)
fen.resizable(False,False)
fen.iconphoto(True,photoMicroicon)
fen.mainloop()
