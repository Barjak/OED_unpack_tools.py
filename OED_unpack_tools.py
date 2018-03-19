#!/usr/bin/env python3
# OED_unpack_tools.py -- Unpack the 'oed.t' blob included in the OED CD-ROM, then spit out JSON
# Copyright (C) 2018 Jakob Barger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import sys
import os
import zlib
import math
import multiprocessing
import concurrent.futures
import time
import argparse
import hashlib
import collections

from parse import Parse

OFFSET_FILENAME="oed.t.offsets"

OEDT_SHA512 = "fd0b2bbfedd23adfba22fbc18eb7492877a467807270d8286db89dbe4e3b612183d4d103420f74e7a4d04430a8d1cb80b0bdf5a67e7a54d926e6bffc152b603f"

OutputInfo = collections.namedtuple('OutputInfo', ['raw', 'json', 'begin', 'end'])

def sha512sum(file):
    h = hashlib.sha512()
    for block in iter(lambda: file.read(100000), b''):
        h.update(block)
    return h.hexdigest()

def convert(info):
    convert_UTF8 = info[4]
    with open(info[0], 'r') as in_file:
        with open(info[1], 'w') as out_file:
            parse = Parse(convert_UTF8)
            out_file.write(parse.parseToJSON(in_file.read()))
    return info

def decompress_block(stream_in, begin, end):
    stream_in.seek(begin)
    buff = bytearray(stream_in.read(end - begin))
    # Here's the magic part
    buff[0] = 120; buff[1] = 218
    try:
        text = zlib.decompress(buff)
    except:
        raise RuntimeError("Decompress error")
    return text

def main():
    parser = argparse.ArgumentParser(prog='OED_unpack_tools.py')
    parser.add_argument('--input', '-i', '--oed.t', nargs='?', type=argparse.FileType('rb'), required=True, metavar='FILE',
                        help="The path to the input file. It will be named oed.t")
    parser.add_argument('--output-dir', default='./output/', metavar='DIR', help='The output and working directory. (default=./output/)')
    parser.add_argument('--dump-raw', action='store_true', help="Don't parse the files after extraction.")
    parser.add_argument('--jobs', default=1, type=lambda x: max(1, int(x)), metavar='N', help='The number of concurrent parsers to use.')
    parser.add_argument('--convert-UTF8', action='store_true', help='Convert entities to UTF8. Otherwise just use HTML entities.')

    arguments = parser.parse_args()
    out_dir = arguments.output_dir

    # Make sure the file is correct.
    if sha512sum(arguments.input) != OEDT_SHA512:
        raise RuntimeError("Checksum failure. This is not the right input file.")
    else:
        print("Correct checksum")
    # Load list of block offsets.
    try:
        offset_file = open(OFFSET_FILENAME, 'r')
    except (OSError, IOError):
        raise RuntimeError("Can't open offset file.")
    offsets = [
        int(l)
        for l in iter(offset_file.readline, '')
    ]
    # Gather output file information into one list.
    io_info = [
        OutputInfo("%d" % (b), "%d.json" % b, b, e)
        for b,e in zip(offsets, offsets[1:])
    ]
    # Make the output directory if necessary.
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        raise RuntimeError("Can't create output directory")

    print("Decompressing...")
    # Get the set of filenames in the output directory
    fileset = {
        entry.name
        for entry in os.scandir(out_dir)
        if entry.is_file()
    }
    # If neither the raw dump nor the parsed output are found
    # or --dump-raw is specified
    # then schedule extraction.
    files_needing_extraction = [
        info
        for info in io_info
        if (
            (info.raw not in fileset and info.json not in fileset)
            or
            (info.raw not in fileset and arguments.dump_raw)
        )
    ]
    # Extract.
    count = 0
    for info in files_needing_extraction:
        count += 1
        sys.stdout.write('\r  %.1f%%' % (100 * count / len(files_needing_extraction)))
        try:
            file_output = open(os.path.join(out_dir, info.raw), 'wb')
        except (OSError, IOError):
            raise RuntimeError("Can't create output file.")

        file_output.write(decompress_block(arguments.input, info.begin, info.end))
        file_output.close()

    # If dump_raw then we're done here.
    if arguments.dump_raw:
        print("\rDone.")
        exit(0)

    print("\rParsing...")

    fileset = {
        entry.name
        for entry in os.scandir(out_dir)
        if entry.is_file()
    }
    # If a raw file hasn't been deleted yet, then it's either this script's
    # first execution or an interrupt might have happened during parse.
    thread_args = list([
        (os.path.join(out_dir, info.raw), os.path.join(out_dir, info.json), info.begin, info.end, arguments.convert_UTF8)
        for info in io_info
        if (
            info.raw in fileset
        )
    ])
    # Parse. Remove raw file when done to signal completion.
    start = time.time()
    count = 0
    with concurrent.futures.ProcessPoolExecutor(arguments.jobs) as ex:
        for info in ex.map(convert, thread_args):
            os.remove(info[0])
            count += 1
            time_per_file = (time.time() - start) / count
            time_remaining = time_per_file * (len(thread_args) - count)
            sys.stdout.write('\r  %.1f%% Time Remaining: %d:%02d         ' % (100 * count / len(thread_args), time_remaining // 60, time_remaining % 60))

    print("Done.")


if __name__ == "__main__":
    main()
