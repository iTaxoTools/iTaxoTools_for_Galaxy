
# Fichier stub mypy pour openpyxl.

from typing import List,Iterator,Sequence

def load_workbook(fich: str, read_only: bool) -> Book:...

class Book:
    def __getitem__(self,sh: str) -> Sheet:...
    worksheets: List[Sheet]
    sheetnames: List[str]

class Sheet:
    title: str
    def iter_rows(self, values_only:bool) -> Iterator[Sequence]:...
