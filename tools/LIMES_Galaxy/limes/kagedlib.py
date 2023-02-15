
from __future__ import annotations

import sys as _sys

from typing import Optional,List,TextIO

def get_exc_msg(exc: BaseException,titre: bool =False,
                ctxt: bool =True,init: Optional[str] =None) -> List[str]:
    m=str(exc).split('\n') if init is None else [init]
    if titre:
        t=type(exc).__name__+": "
        indent=" "*len(t)
        m2=[]
        for s in m:
            m2.append(t+s)
            t=indent
        m=m2
    if ctxt and isinstance(exc,Exception):
        # BaseException n'a pas de __cause__ ni __context__
        if exc.__cause__ is not None:
            m.extend(get_exc_msg(exc.__cause__,titre,ctxt))
        elif exc.__context__ is not None and not exc.__suppress_context__:
            emis=exc.__traceback__
            if emis is None or exc.__context__.__traceback__ is None:
                ok=True
                # Si __traceback__ n'existe pas, on ignore la recherche
                # intelligente qui suit et on capture systématiquement le
                # contexte. __traceback__ est notamment mis à None dans la
                # clause assertRaisesRegex() de unittest.
            else:
                recep=exc.__context__.__traceback__.tb_frame.f_code.co_name
                while emis.tb_next:
                    emis=emis.tb_next
                ok=emis.tb_frame.f_code.co_name==recep
            if ok:
                m.extend(get_exc_msg(exc.__context__,titre,ctxt))
    return m

def print_error(exc: Optional[BaseException] =None,titre: bool =False,
                ctxt: bool =True,file: TextIO =_sys.stderr) -> None:
    if exc is None:
        exc=_sys.exc_info()[1]
        if exc is None:
            print("(pas d'exception courante)")
            return
    for lg in get_exc_msg(exc,titre,ctxt):
        print(lg,file=file)
