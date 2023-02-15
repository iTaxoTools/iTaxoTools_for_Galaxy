
This is the Limes package.

Creation: 29 March 2021 : v.2.0
Author: Jacques Ducasse

Versions :
10 April 2012 : v.2.0.1

Content
-------

limes
	Python package of Limes

doc
	Collection of docs

mkexe
	Tools to create executable version, and executables

Using Limes
-----------

"limes" is an executable package: you have to "import" the package directory.
Thus, include the "limes" parent directory in PYTHONPATH, then :

	% python -m limes

See :
	% python -m limes -hh
for the complete command line syntax.

Prerequisite
------------

- Python version needed : 3.7 or above.

- If you want to load .xls files, you need to install the "xlrd" package :
	https://pypi.org/project/xlrd/

- If you want to load .xlsx files, you need to install the "openpyxl" package :
	https://pypi.org/project/openpyxl/
