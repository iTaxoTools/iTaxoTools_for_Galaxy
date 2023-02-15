
"""
Tableur implémenté par un Canvas.

Le module propose les classes suivantes :
    Tableur
    STableur

Auteur : J.Ducasse, février 2019
"""

from tkinter import *
from tkinter.ttk import *

__all__=("Tableur","STableur")

INTERESP_X=2    # espace entre 2 colonnes
INTERESP_Y=2    # espace entre deux lignes
HAUTEUR_LG=18   # hauteur d'un ligne (non inclus l'inter-espace)
TOTAL_LG=INTERESP_Y+HAUTEUR_LG
                # hauteur totale d'une ligne
OFFSET_TXT=9    # offset du texte (centré verticalt) par rapport au haut du cadre
ORIGINE_COL=0   # abscisse des colonnes nouvellement créées
INIT_SEPAR=HIDDEN
                # Etat initial des spéarateurs NORMAL/HIDDEN
COLOR_SEPAR="#808080"
COLOR_FOND="#f2f2f2"
DEBUG_DEL=False

"""
Cellule(can,col,numlg,txttag,rectag)

Crée une cellule dans le Canvas 'can, à l'intersection de la colonne 'col
(instance de Colonne) et de la ligne de numéro 'numlg (>=0). La Cellule comprend
un item text, de tag 'txttag, et un item rectangle, de tag 'rectag.
Note : la fourniture de 'col est facultative à la création ; cependant, si
'col n'est pas fourni, l'appelant doit positionnner l'attribut .col à
l'instance de Colonne possédant cette cellule avant toute autre action sur la
cellule.

L'instance dispose des attributs suivants :
    .txt        L'item texte.
    .rec        L'item rectangle (fond).
    .numlg      Le numéro de ligne (>=0).
    .indlg      L'indice de la ligne (>=0) dans son Canvas.
    .col        L'instance de Colonne.
    .can        Le Canvas.
    .handler    True si la cellule réagit au clic, False sinon.
"""
class Cellule:
    __slots__=("rec","txt","numlg","indlg","col","can","handler")
    def __init__(self,can,col,numlg,txttag,rectag):
        self.rec=can.create_rectangle(0,0,0,0,tags=rectag,fill=COLOR_FOND,
                                      width=0)
        self.txt=can.create_text(0,0,tags=txttag,anchor=CENTER)
        self.numlg=numlg
        self.indlg=max(0,numlg-1)
        self.col=col
        self.can=can
        self.handler=False
        self.resize()
        self.anchor()

    def __del__(self):
        if DEBUG_DEL:
            print("del Cellule %dx%d"%(self.indlg,self.numlg))

    def destroy(self):
        self.indlg=self.col.numcol # pour __del__() !
        del self.col,self.can

    """
    Redimensionne la cellule et repositionne les éléments (rectangle et texte)
    en fonction de la position et de la largeur de la colonne à laquelle elle
    appartient.
    """
    def resize(self):
        col=self.col
        y0=self.indlg*TOTAL_LG+INTERESP_Y
        y1=y0+HAUTEUR_LG
        self.can.coords(self.rec,col.x,y0,col.x+col.larg,y1)
        self.anchor()

    """
    Affecte l'ancre de l'item texte à 'anchor, qui doit valoir W, E ou CENTER,
    et repositionne l'item. Si 'anchor vaut None, repositionne l'item
    conformément à la valeur courante de l'ancre.
    """
    def anchor(self,anchor=None):
        col=self.col
        if anchor is None: anchor=self.can.itemcget(self.txt,"anchor")
        if anchor==W:
            x=col.x+col.padx
        elif anchor==E:
            x=col.x+col.larg-col.padx
        elif anchor==CENTER:
            x=col.x+col.larg/2
        else:
            return
        self.can.itemconfigure(self.txt,anchor=anchor)
        self.can.coords(self.txt,x,self.indlg*TOTAL_LG+INTERESP_Y+OFFSET_TXT)

"""
Crée un séparateur dans le Canvas 'can. Le séparateur est vertical si 'vert
vaut True, horizontal sinon.
Le séparateur est composé de deux traits, l'un dans la couleur COLOR_SEPAR,
l'autre blanc. Les deux items sont associés au tag 'tag.
"""
class Separateur:
    def __init__(self,can,vert,tag,x1,y1,x2,y2):
        self.can=can
        self.vert=vert
        self.sep1=can.create_line(x1,y1,x2,y2,
                                  state=INIT_SEPAR,tags=tag,fill=COLOR_SEPAR)
        self.sep2=can.create_line(*self.__newcoords(x1,y1,x2,y2),
                                  state=INIT_SEPAR,tags=tag,fill="white")

    def __del__(self):
        if DEBUG_DEL:
            print("del SEPAR")

    def __newcoords(self,x1,y1,x2,y2):
        return (x1+1,y1,x2+1,y2) if self.vert else (x1,y1+1,x2,y2+1)

    def coords(self,x1,y1,x2,y2):
        self.can.coords(self.sep1,x1,y1,x2,y2)
        self.can.coords(self.sep2,*self.__newcoords(x1,y1,x2,y2))

"""
Colonne(can,col,nblg,canH=None)

Crée la colonne de numéro 'col (>=0) dans le Canvas 'can. 'nblg est le nombre
de lignes. Si 'canH!=None, crée la Cellule correspondant dans le Canvas 'canH.
L'instance de Colonne est une liste dont les éléments sont les Cellule, chacune
correspondant à l'intersection de la colonne et d'une ligne. L'indexation et
l'itération n'incluent pas la Cellule de titre.

L'instance dispose des attributs et méthodes suivants :
    .can        Le Canvas 'can passé en argument (Canvas principal ou titre
                gauche).
    .canT       Le Canvas 'canH passé en argument, ou None.
    .cellT      La Cellule dans 'canH, ou None.
    .x          L'abscisse du bord gauche de la colonne dans son Canvas.
    .larg       Largeur de la colonne.
    .numcol     Numéro de la colonne (>=0).
    .indcol     Indice de la colonne (>=0) dans son Canvas.
    .txttag
    .rectag
    .septag
    .minsize
    .padx
    .maj()
    .find_cell()
"""
class Colonne(list):
    def __init__(self,can,col,nblg,canH=None):
        self.txttag=txttag="txtCol%d"%col
        self.rectag=rectag="recCol%d"%col
        self.septag=septag="sepCol%d"%col
        self.x=ORIGINE_COL
        self.larg=10
        self.minsize=0
        self.padx=2
        self.numcol=col
        self.indcol=max(col-1,0)
        for i in range(1,nblg+1):
            self.append(Cellule(can,self,i,txttag,rectag))
            # Colonne ne peut être dérivée de tuple, plutôt que list, car on
            # doit passer 'self au constructeur de Cellule ; or les Cellule
            # doivent préexister au tuple, qui est immutable !
        x=self.x+self.larg
        Separateur(can,True,septag,x,INTERESP_Y,x,nblg*TOTAL_LG)
        if canH:
            self.cellT=Cellule(canH,self,0,txttag,rectag)
            Separateur(canH,True,septag,x,INTERESP_Y,x,TOTAL_LG)
        else:
            self.cellT=None
        self.can=can
        self.canT=canH

    def __del__(self):
        if DEBUG_DEL:
            print("del COLONNE %d"%self.numcol)

    def destroy(self):
        for c in self: c.destroy()
        if self.canT: self.cellT.destroy()
        del self.can,self.canT

    """
    Rend la Cellule dont le rectangle égale 'item, ou None si non trouvé.
    """
    def find_cell(self,item):
        for c in self:
            if c.rec==item:
                return c

    """
    Repositionne les cellules de la colonne. 'gch est la Colonne immédiatement
    à gauche, ou None s'il n'y en a pas.
    """
    def maj(self,gch):
        txttag=self.txttag
        a,_,b,_=self.can.bbox(txttag)
        new_larg=b-a
        if self.canT:
            a,_,b,_=self.canT.bbox(txttag)
            new_larg=max(new_larg,b-a)
        new_larg+=self.padx*2
        new_larg=max(new_larg,self.minsize)
        x,larg=self.x,self.larg
        if gch:
            new_x=gch.x+gch.larg+INTERESP_X
        else:
            new_x=0
        resize=new_larg-larg
        mvtag=txttag
        if resize==0: mvtag+="||"+self.septag+"||"+self.rectag
        mv=new_x-x
        self.can.move(mvtag,mv,0)
        if self.canT:
            self.canT.move(mvtag,mv,0)
        self.x=new_x
        self.larg=new_larg
        if resize:
            depsep=resize+mv
            self.can.move(self.septag,depsep,0)
            for c in self: c.resize()
            if self.canT:
                self.cellT.resize()
                self.canT.move(self.septag,depsep,0)

"""
Ligne(numlg,cols,colG)

Crée la ligne de numéro 'numlg (>=0). 'cols est la liste des Colonne dans le
Canvas principal ; 'colG est la colonnne de titre gauche, ou None.
Les Cellule ne sont pas créées ; on suppose qu'elles ont été créées auparavant
dans les Colonne.
L'instance de Ligne est itérable et indexable. L'itération donne la liste des
Cellule (non inclus le titre gauche). lg[indcol] rend la Cellule de la ligne
pour la colonne d'indice 'indcol. L'indexation et l'itération n'incluent pas la
Cellule de titre.

L'instance dispose des attributs et méthodes suivants :
    .can        Le Canvas de la ligne (Canvas principal ou Canvas titre haut).
    .canT       Le Canvas de la colonne de gauche, ou None.
    .cellT      La Cellule dans 'canG, ou None.
    .numlg      Le numéro de la ligne (>=0).
    .indlg      L'indice de la ligne (>=0) dans son Canvas.
    .txttag
    .rectag
    .septag
    .maj()
"""
class Ligne:
    __slots__=("_Ligne__colonnes","_Ligne__colG","numlg","indlg","can","canT",
               "txttag","rectag","_Ligne__separ","_Ligne__separT","septag")

    def __init__(self,numlg,cols,colG):
        self.__colonnes=cols
        self.__colG=colG
        self.numlg=numlg
        self.indlg=max(0,numlg-1)
        self.can=cols[0].can if numlg else cols[0].canT
        self.canT=colG.can if colG else None
        self.txttag=txttag="txtLg%d"%numlg
        self.rectag=rectag="recLg%d"%numlg
        self.septag=septag="sepLg%d"%numlg
        for c in self:
            c.can.addtag_withtag(txttag,c.txt)
            c.can.addtag_withtag(rectag,c.rec)
        if colG:
            c=self.cellT
            c.can.addtag_withtag(txttag,c.txt)
            c.can.addtag_withtag(rectag,c.rec)
        self.__separ=Separateur(self.can,False,septag,0,0,0,0)
        if colG:
            self.__separT=Separateur(self.canT,False,septag,0,0,0,0)
        self.maj()

    def __del__(self):
        if DEBUG_DEL:
            print("del LIGNE %d"%self.numlg)

    def destroy(self):
        del self.__colonnes,self.__colG

    def __getitem__(self,indcol):
        if self.numlg: return self.__colonnes[indcol][self.indlg]
        return self.__colonnes[indcol].cellT

    def __iter__(self):
        for col in self.__colonnes:
            yield (col[self.indlg] if self.numlg else col.cellT)

    @property
    def cellT(self):
        return self.__colG[self.indlg] if self.__colG else None

    def maj(self):
        y=(self.indlg+1)*TOTAL_LG+1
        x=self.__colonnes[-1].x+self.__colonnes[-1].larg
        self.__separ.coords(0,y,x,y)
        if self.__colG:
            x=self.__colG.x+self.__colG.larg
            self.__separT.coords(0,y,x,y)

"""
Tableur(parent,nbcol,nblg,titreH=True,titreG=True,handler=None)

Crée un tableur de 'nbcol colonnes et 'nblg lignes. Le tableur est aussi muni
d'un ligne de titre (en haut) et/ou d'une colonne de titre (à gauche) si
'titreH et/ou 'titreG vaut True. 'handler est la fonction qui sera appelée au
clic sur les cellules dont l'option "handler" aura été mise à True (voir
config_cellule()).

Pour toutes les fonctions recevant en argument un numéro de ligne ou de colonne,
celles-ci sont comptées à partir de 1 (en haut ou à gauche). La ligne de titre
et la colonne de titre, si elles existent, ont le numéro 0. Une exception est
générée si le numéro de ligne ou de colonne fourni est invalide.

La plupart des fonctions possèdent une option "maj", à False par défaut. Si
True, le dessin du tableur est immédiatement mis à jour avant le retour de la
fonction. Si False, le dessin ne sera mis à jour que suite à l'appel d'une autre
fonction avec 'maj à True, ou de façon forcée par un appel à .maj(). Si l'on
doit réaliser un grand nombre de modifications, il est préférable d'appeler les
fonctions avec 'maj à False, puis de forcer la mise à jour seulement à la fin.

L'instance dispose des attributs et méthodes suivants :
    .handler    La fonction 'handler passée en argument. Cet attribut peut être
                réaffecté à tout moment.
    .nbcol      Le nombre de colonnes.
    .nblg       Le nombre de lignes.
    .setligne()
    .settitreH()
    .setcolonne()
    .settitreG()
    .setcellule()
    .config_colonne()
    .config_ligne()
    .config_cellule()
    .maj()
"""
class Tableur(Frame):
    def __init__(self,parent,nbcol,nblg,titreH=True,titreG=True,handler=None):
        super().__init__(parent)
        s=Style()
        s.configure("Tab.TFrame",background=COLOR_FOND)
        self.configure(style="Tab.TFrame")
        self._can=can=Canvas(self,bg=COLOR_FOND)
        can.grid(row=1,column=1,sticky=NSEW)
        _handler=self.__handler
        can.bind("<Button-1>",_handler)
        if titreH:
            titreH=Canvas(self,bg=COLOR_FOND)
            titreH.grid(row=0,column=1,sticky=NSEW)
            titreH.bind("<Button-1>",_handler)
        else:
            titreH=None
        self._titreH=titreH
        if titreG:
            titreG=Canvas(self,bg=COLOR_FOND)
            titreG.grid(row=1,column=0,sticky=NSEW)
            titreG.bind("<Button-1>",_handler)
            self.__col_titreG=Colonne(titreG,0,nblg)
        else:
            titreG=None
        self._titreG=titreG

        self.columnconfigure(1,weight=1)
        self.rowconfigure(1,weight=1)

        self.__colonnes=[Colonne(can,i,nblg,titreH) for i in range(1,nbcol+1)]

        self.__lignes=[Ligne(i,self.__colonnes,self.__col_titreG)
                       for i in range(1,nblg+1)]
        self.__lg_titreH=Ligne(0,self.__colonnes,self.__col_titreG) if titreH \
                                                                    else None
        self.nbcol=nbcol
        self.nblg=nblg
        self.handler=handler
        self._can=self._can

    def __del__(self):
        if DEBUG_DEL:
            print("del Tableur")

    def destroy(self):
        for c in self.__colonnes: c.destroy()
        if self._titreG: self.__col_titreG.destroy()
        for c in self.__lignes: c.destroy()
        if self._titreH: self.__lg_titreH.destroy()
        del self._titreH,self._titreG,self._can,self.__colonnes
        del self.__col_titreG
        del self.__lignes,self.__lg_titreH
        super().destroy()

    """
    Rend la Cellule correspondant à l'intersection de la colonne 'numcol et de
    la ligne 'numlg. 'numcol ou 'numlg peuvent valoir 0 pour la colonne ou la
    ligne de titre
    """
    def __ok_cell(self,numcol,numlg):
        if numcol==numlg==0:
            raise ValueError("Intersection 0x0 invalide")
        col=self.__ok_col(numcol)
        lg=self.__ok_ligne(numlg)
        return col.cellT if lg.numlg==0 else col[lg.indlg]

    """
    Vérifie si 'numcol est un numéro de colonne valide. Rend la Colonne
    correspondante si ok.
    Sinon, génère une exception ValueError.
    """
    def __ok_col(self,numcol):
        if numcol==0:
            if self._titreG:
                return self.__col_titreG
        else:
            if 1<=numcol<=self.nbcol:
                return self.__colonnes[numcol-1]
        raise ValueError("Numéro de colonne invalide")

    """
    Vérifie si 'numlg est un numéro de ligne valide. Rend la Ligne
    correspondante si ok.
    Sinon, génère une exception ValueError.
    """
    def __ok_ligne(self,numlg):
        if numlg==0:
            if self._titreH:
                return self.__lg_titreH
        else:
            if 1<=numlg<=self.nblg:
                return self.__lignes[numlg-1]
        raise ValueError("Numéro de ligne invalide")

    """
    Affecte le libellé de toutes les cellules de la ligne 'numlg avec ceux de la
    liste 'labels, qui doit comporter autant d'éléments qu'il y a de colonnes.
    La colonne de titre n'est pas concernée.
    """
    def setligne(self,numlg,labels,maj=False):
        lg=self.__ok_ligne(numlg)
        if len(labels)!=self.nbcol:
            raise ValueError("Nombre de libellés invalide")
        can=lg.can
        for it,lab in zip(lg,labels):
            can.itemconfigure(it.txt,text=lab)
        self.maj(maj)

    """
    Comme setligne(), spécialisée pour la ligne de titre haut.
    """
    def settitreH(self,labels,maj=False):
        self.setligne(0,labels,maj)

    """
    Affecte le libellé de toutes les cellules de la colonne 'numcol avec ceux
    de la liste 'labels, qui doit comporter autant d'éléments qu'il y a de
    lignes. La ligne de titre n'est pas concernée.
    """
    def setcolonne(self,numcol,labels,maj=False):
        col=self.__ok_col(numcol)
        if len(labels)!=self.nblg:
            raise ValueError("Nombre de libellés invalide")
        can=col.can
        for it,lab in zip(col,labels):
            can.itemconfigure(it.txt,text=lab)
        self.maj(maj)

    """
    Comme setcolonne(), spécialisée pour la colonne de titre gauche.
    """
    def settitreG(self,labels,maj=False):
        self.setcolonne(0,labels,maj)

    """
    Affecte à 'label le libellé de la cellule à l'intersection de la colonne
    'numcol et de la ligne 'numlg.
    """
    def setcellule(self,numcol,numlg,label,maj=False):
        cell=self.__ok_cell(numcol,numlg)
        cell.can.itemconfigure(cell.txt,text=label)
        self.maj(maj)

    """
    Si 'mod vaut True, met à jour et redessine l'ensemble du tableur. Cette
    fonction doit être appelée après une série de modifications faites sans
    mise à jour. Si 'mod vaut False, ne fait rien !
    """
    def maj(self,mod=True):
        if mod:
            if self._titreG:
                col=self.__col_titreG
                col.maj(None)
                xg,yh,xd,yb=self._titreG.bbox(ALL)
                self._titreG.config(width=xd-xg,height=yb-yh,
                                    scrollregion=(xg,yh,xd,yb))
            for i,col in enumerate(self.__colonnes):
                col.maj(self.__colonnes[i-1] if i else None)
            for lg in self.__lignes:
                lg.maj()
            if self.__lg_titreH:
                self.__lg_titreH.maj()

            xg,yh,xd,yb=self._can.bbox(ALL)
            if self._titreH:
                xg2,yh2,xd2,yb2=self._titreH.bbox(ALL)
                xg=min(xg,xg2)
                xd=max(xd,xd2)
            self._can.config(scrollregion=(xg,yh,xd,yb),
                             width=xd-xg,height=yb-yh)
            if self._titreH:
                self._titreH.config(scrollregion=(xg,yh2,xd,yb2),
                                    width=xd-xg,height=yb2-yh2)

    def __config_lgcol(self,iscol,num,minsize=None,separ=None,titre=False,
                       anchor=None,color=None,handler=None,label=None,padx=None,
                       maj=False):
        if not (self._titreG if iscol else self._titreH): titre=False
        if isinstance(num,int): num=[num]
        elif num==ALL: num=list(range(1,(self.nbcol if iscol else self.nblg)+1))
        for num in num:
            titre2=titre
            if num==0: titre2=False
            lgcol=(self.__ok_col if iscol else self.__ok_ligne)(num)
            if minsize is not None:
                if iscol: lgcol.minsize=minsize
            if separ is not None:
                state=NORMAL if separ else HIDDEN
                lgcol.can.itemconfigure(lgcol.septag,state=state)
                if titre2:
                    lgcol.canT.itemconfigure(lgcol.septag,state=state)
            if color is not None:
                lgcol.can.itemconfigure(lgcol.rectag,fill=color)
                if titre2:
                    c=lgcol.cellT
                    c.can.itemconfigure(c.rec,fill=color)
            if padx is not None:
                if iscol:
                    lgcol.padx=padx
            if label is not None:
                lgcol.can.itemconfigure(lgcol.txttag,text=label)
                if titre2:
                    c=lgcol.cellT
                    c.can.itemconfigure(c.txt,text=label)
            if handler is not None:
                for c in lgcol: c.handler=handler
                if titre2: lgcol.cellT.handler=handler
            if anchor is not None:
                for c in lgcol: c.anchor(anchor)
                if titre2: lgcol.cellT.anchor(anchor)
        self.maj(maj)

    """
    Affecte les paramètres de toutes les cellules de la colonne 'col. Les
    paramètres disponibles sont :
        minsize     Largeur minimale (en pixels).
        separ       Si True, un séparateur est dessiné entre la colonne et sa
                    voisine de droite. Si False, pas de séparateur.
        *anchor     W, E ou CENTER : position du texte dans la cellule. CENTER
                    à la création du tableur.
        *color      Couleur de fond des cellules.
        *label      Affecte le libellé de toutes les cellules à 'label.
        padx        Marge à droite et à gauche. [On peut fournir une marge, qui
                    s'appliquera à droite et à gauche, ou un couple (gauche,
                    droite). Non encore implémenté]
        *handler    Si True, la fonction handler positionnée sur le Tableur
                    sera appelée lorsque l'on clique sur la cellule, avec 2
                    arguments : numéro de colonne et numéro de ligne. False par
                    défaut.
        titre       Si True, les options (marquées d'un astérisque) s'appliquent
                    à toute la colonne, y compris la cellule de la ligne de
                    titre. Si False, la cellule de la ligne de titre n'est pas
                    affectée. False par défaut. Ignorée si pas de ligne de
                    titre.
        maj         Force la mise à jour si True.False par défaut.
    Les options non fournies ou à None sont ignorées.
    'col peut être un simple numéro de colonne, ou une liste de numéros, ou ALL
    pour toutes les colonnes (sauf celle de titre).
    """
    def config_colonne(self,col,**kw):
        self.__config_lgcol(True,col,**kw)

    """
    Affecte les paramètres de toutes les cellules de la ligne 'ligne. Les
    paramètres disponibles sont :
        minsize     Hauteur minimale (en pixels). [non implémenté]
        separ       Si True, un séparateur est dessiné entre la ligne et sa
                    voisine en-dessous. Si False, pas de séparateur.
        *anchor     Idem config_colonne().
        *color      Idem config_colonne().
        *label      Idem config_colonne().
        padx        Idem config_colonne(). [non implémenté]
        *handler    Idem config_colonne().
        titre       Si True, les options (marquées d'un astérisque) s'appliquent
                    à toute la ligne, y compris la cellule de la colonne de
                    titre. Si False, la cellule de la colonne de titre n'est pas
                    affectée. False par défaut. Ignorée si pas de colonne de
                    titre.
        maj         Force la mise à jour si True.False par défaut.
    Les options non fournies ou à None sont ignorées.
    'ligne peut être un simple numéro de ligne, ou une liste de numéros, ou ALL
    pour toutes les lignes (sauf celle de titre).
    """
    def config_ligne(self,lg,**kw):
        self.__config_lgcol(False,lg,**kw)

    """
    Affecte les paramètre de la cellule à l'intersection de la colonne 'col et
    de la ligne 'ligne. Les options ont la même signification que pour
    config_colonne(), mais ne s'appliquent qu'à une seule cellule.
    """
    def config_cellule(self,col,ligne,anchor=None,color=None,label=None,
                       handler=None,maj=False):
        cell=self.__ok_cell(col,ligne)
        if anchor is not None:
            cell.anchor(anchor)
        if color is not None:
            cell.can.itemconfigure(cell.rec,fill=color)
        if label is not None:
            cell.can.itemconfigure(cell.txt,text=label)
        if handler is not None:
            cell.handler=handler
        self.maj(maj)

    def __handler(self,ev):
        if self.handler:
            cell=None
            can=ev.widget
            x,y=can.canvasx(ev.x),can.canvasy(ev.y)
            for it in can.find_overlapping(x,y,x,y):
                if can.type(it)=="rectangle":
                    if can==self._titreG:
                        cell=self.__col_titreG.find_cell(it)
                    elif can==self._titreH:
                        for c in self.__lg_titreH:
                            if c.rec==it:
                                cell=c
                                break
                    else:
                        for col in self.__colonnes:
                            cell=col.find_cell(it)
                            if cell: break
                    if cell and cell.handler:
                        self.handler(cell.col.numcol,cell.numlg)
                    break

"""
Version scrollable de Tableur.
Identique à Tableur, avec un ascenseur horizontal et un ascenceur vertical.
"""
class STableur(Tableur):
    def __init__(self,parent,*args,**kw):
        super().__init__(parent,*args,**kw)
        if self._titreH:
            def xview(*args,**kw):
                self._can.xview(*args,**kw)
                self._titreH.xview(*args,**kw)
        else:
            xview=self._can.xview
        if self._titreG:
            def yview(*args,**kw):
                self._can.yview(*args,**kw)
                self._titreG.yview(*args,**kw)
        else:
            yview=_can.yview
        vsb=Scrollbar(self,orient=VERTICAL,command=yview)
        vsb.grid(row=1,column=2,sticky=NSEW)
        hsb=Scrollbar(self,orient=HORIZONTAL,command=xview)
        hsb.grid(row=2,column=1,sticky=NSEW)
        self._can.config(yscrollcommand=vsb.set,xscrollcommand=hsb.set)


##fen=Tk()
##fen.rowconfigure(1,weight=1)
##fen.columnconfigure(1,weight=1)
##t=STableur(fen,5,3)
##t.grid(row=1,column=1,sticky=NSEW)
##t.setligne(2,("xx","fff","rrrr","aaaa","ttt"))
##t.settitreH(("aa","bbb","c","dddd","ee"))
####t.config_colonne((0,5),minsize=50)
####t.config_colonne(5,anchor=W)
####t.config_colonne(5,anchor=W,titre=True)
##t.settitreG(("111","222","33333"))
##t.maj()
##t.setligne(3,("333333","33","33333333","3","3"),True)
##def ff(a,b):
##    print(a,b)
##t.config_ligne(2,handler=True)
##t.handler=ff

##t.setligne(3,("333333","33","33333333","3","3"),True)
##t.settitreH(("aaaa","bbbbbbbbb","cc","ddddddddd","e"),True)
##t.settitreG(("1111111","22","3"),True)
##t.setcellule(0,3,"aaaaaa",True)
##t.setcellule(0,3,"aaaaaammmmm",True)
