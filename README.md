
# OED_unpack_tools.py

The Oxford English Dictionary published a version of the dictionary on CD. It is a terrible program. It is a Windows app written in Neko/Haxe/Flash with a very obscure widget library called SWHX.

Turns out the file `oed.t` is about 1000 zlib archives concatenated together with their headers zeroed out. I think the entries are stored in something like SGML, and this program attempts to parse them. Many thanks to Neni @failortwist for discovering a table of nonstandard character entity references contained in `OED.swf`.

The script unpacks all 1000 raw files, then it parses it with PyParsing (taking care to substitute entity references), then it restructures it as 1000 JSON files, then it deletes the raw files. <sub><sup>(The JSON output leaves a lot to be desired I feel. Feel free to contribute.)</sup></sub>

### Dependencies:
* [Anaconda](https://www.anaconda.com/distribution/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### Setup:
~~~~
cd OED_unpack_tools.py/
./setup.sh
conda activate oedenv
pypy3 OED_unpack_tools.py -i ~/path/to/oed.t --jobs 8
conda deactivate
~~~~

You can also just use regular CPython etc. but it takes 5 times longer.

### Usage
~~~~
usage: OED_unpack_tools.py [-h] --input [FILE] [--output-dir DIR] [--dump-raw]
                           [--jobs N] [--convert-UTF8]

optional arguments:
  -h, --help            show this help message and exit
  --input [FILE], -i [FILE], --oed.t [FILE]
                        The path to the input file. It will be named oed.t
  --output-dir DIR      The output and working directory. (default=./output/)
  --dump-raw            Don't parse the files after extraction.
  --jobs N              The number of concurrent parsers to use.
  --convert-UTF8        Convert entities to UTF8. Otherwise just use HTML
                        entities.
~~~~

This software does not violate the EULA as far as I'm aware.

Recent changes:
* Add UTF-8 output support
* Use a proper environment
