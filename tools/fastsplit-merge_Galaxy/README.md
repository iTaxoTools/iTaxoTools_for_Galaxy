# fastsplit-merge
fastmerge and fastsplit are simple tools to merge and split large text files, in particular intended for merging/splitting fasta and fastq files. The tools include options to specify search terms in sequence titles and sequence motifs to include/exclude sequences for splitting/merging.

## Installation
Installation is currently not intended. Downloading should be enough

## Generating an executable
Using [PyInstaller](http://www.pyinstaller.org) is recommended. After the following instruction a directory `dist` will be created (among other) and the executable will be inside it.

### Linux
Install PyInstaller from PyPI:

    pip install pyinstaller

Then run

    pyinstaller --onefile fastmerge.py

### Windows
Install PyInstaller:

[Installing on Windows](https://pyinstaller.readthedocs.io/en/stable/installation.html#installing-in-windows)

Then run

    pyinstaller --onefile --windowed fastmerge.py

## Fastmerge

### Usage
    usage: fastmerge.py [-h] [--cmd] [--fasta | --fastq] [--seqid PATTERN]
                        [--sequence PATTERN]
           fastmerge.py
    
    optional arguments:
      -h, --help          show this help message and exit
      --cmd               Launches in the command-line mode
      --fasta             Process only .fas and .fas.gz files
      --fastq             Process only .fq, .fq.gz, .fastq and .fastq.gz files
      --seqid PATTERN     Filter pattern for sequence names
      --sequence PATTERN  Filter pattern for sequences

### Command-line interface
Fastmerge reads the list of files and directories from the standard input and merges them into one file. For each directory, it merges the files inside it.
It uncompresses the gzip archives if necessary. The output is written to the standard output. 

When --seqid or --sequence and either --fasta or --fastq options are given, only the sequence records matching the patterns are written to the output.

## Fastsplit

### Usage
    usage: fastsplit.py [-h] [--fasta | --fastq | --text] [--split_n SPLIT_N | --maxsize MAXSIZE | --seqid PATTERN | --sequence PATTERN] [--compressed]
                        [infile] [outfile]
    
    positional arguments:
      infile              Input file name
      outfile             Output file template
    
    optional arguments:
      -h, --help          show this help message and exit
      --fasta             Input file is a fasta file
      --fastq             Input file is a fastq file
      --text              Input file is a text file
      --split_n SPLIT_N   number of files to split into
      --maxsize MAXSIZE   Maximum size of output file
      --seqid PATTERN     split the records that match the sequence identifier pattern
      --sequence PATTERN  split the records that match the sequence motif pattern
      --compressed        Compress output files with gzip

### Command-line interface
Fastsplit reads the input file and splits into files according to the options.
Currently supported formats are FASTA and FastQ. Arbitrary text files can also be processed, but `seqid` and `sequence` options are not supportd for them.
The spliting criteria are:
* Number of output parts (`split_n`)
* Limit on maximum size of parts (`maxsize`). The size is specified in in the format `{number}{unit}` where unit is one of 'bBkKmMgG'.
    Examples: 165b (165 bytes), 56K (56 kilobytes), 34M (34 Megabytes), 1.5g (1.5 Gigabytes)
* Split into two files: one with records matching a pattern and one with the remaining records:
    * Match the sequence identifier (`seqid`)
    * Match the motifs in the sequence (`sequence`)

Maximum size and the number of output files are only enforced approximately. 


## Filtering
A pattern consists of strings in double quotes, operators 'and', 'or' and 'not' (unquoted) and parentheses. It should be given in single quotes for the command-line interface and unquoted for the GUI.

Examples:
* "Boophis"
* not "Boophis"
* "Boophis" and "Madagascar"
* "Boophis" or "Madagascar"
* ("Boophis" or "Madagascar") and "Ranomafana"
