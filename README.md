# OED_unpack_tools.py

The Oxford English Dictionary published a version of the dictionary on CD. It is a terrible program. It's a barebones GUI written in Neko/Haxe with a very obscure widget library. It's not cross-platform either.

Turns out the file `oed.t` is about 1000 zlib archives concatenated together with their headers zeroed out. I'm not sure exactly how to parse the markup language it uses. I was able to convert their in-house entity references into something more familiar, but it's still not ideal.

The script unpacks all 1000 raw files, then it parses it with PyParsing (taking care to substitute entity references), then it restructures it as 1000 JSON files and deletes the raw files. <sub><sup>(The JSON output leaves a lot to be desired I feel. Feel free to contribute.)</sup></sub>

[Pypy3](https://pypy.org/download.html) is highly recommended if you're going to use the parser. Otherwise it'll take over an hour.

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
  --convert-UTF8        Not yet implemented. Only HTML entity references for
                        now.
~~~~

This software does not violate the EULA as far as I'm aware.