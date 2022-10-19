#!/bin/bash
echo <myinput1 >myinput.txt
file -i myinput.txt &>checktype.txt
if grep 'iso' checktype.txt 
then
    iconv -f ISO-8859-1 -t UTF-8//IGNORE >myinput -o 'input_conv' -c 
else
  cp myinput.txt input_conv2.txt
fi