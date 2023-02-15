
call py37

set NAME=limes

rem version --onedir
rem rmdir /S /Q dist\%NAME%

rem version --onefile
del dist\%NAME%.exe

rmdir /S /Q build\%NAME%

rem Choisir l'option --onefile ou --onedir (défaut).

call C:\Users\jacko\softs\Python37\Scripts\pyinstaller --onefile ^
	--exclude-module select ^
	--exclude-module unicodedata ^
	--exclude-module _bz2 ^
	--exclude-module _elementtree ^
	--exclude-module _hashlib ^
	--exclude-module _lzma ^
	--exclude-module _socket ^
	--exclude-module _ssl ^
	--exclude-module email ^
	--exclude-module html ^
	--exclude-module http ^
	--exclude-module pydoc_data ^
	--exclude-module unittest ^
	--exclude-module pydlib ^
	--exclude-module PIL ^
	--name %NAME% ^
	--windowed ^
	bootlimes.py

rem : ne pas supprimer xml, pyexpat
rem : ne pas supprimer urllib : utilisé par openpyxl
rem : option debug pour voir les fichiers intégrés : --debug noarchive
rem : il introduit canvastableur au top niveau et dans pydlib ->
rem : on supprime pydlib

rem version --onedir
rem del dist\%NAME%\VCRUNTIME140.dll
rem rmdir /S /Q dist\%NAME%\tcl\http1.0
rem rmdir /S /Q dist\%NAME%\tcl\opt0.4
