#!/usr/bin/env python3

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

OUTPUT_PATH=os.path.abspath("./output/")
OFFSET_FILENAME="oed.t.offsets"

OEDT_SHA512 = "fd0b2bbfedd23adfba22fbc18eb7492877a467807270d8286db89dbe4e3b612183d4d103420f74e7a4d04430a8d1cb80b0bdf5a67e7a54d926e6bffc152b603f"

OutputInfo = collections.namedtuple('OutputInfo', ['raw', 'json', 'begin', 'end'])

def sha512sum(file):
    h = hashlib.sha512()
    for block in iter(lambda: file.read(100000), b''):
        h.update(block)
    return h.hexdigest()

def convert(info):
    with open(info[0], 'r') as in_file:
        with open(info[1], 'w') as out_file:
            parse = Parse()
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
    parser = argparse.ArgumentParser(prog='OED-unpack')
    parser.add_argument('--input', '-i', '--oed.t',  nargs='?', type=argparse.FileType('rb'), required=True, metavar='FILE', help='The path to the input file.')
    parser.add_argument('--output-dir', default='./output/', metavar='DIR', help='The output and working directory. (default ./output/)')
    # parser.add_argument('--one-file', action='store_true')
    # parser.add_argument('--leave-working-files', action='store_true', help="Don't delete the raw SGML dumps after they've been parsed.")
    parser.add_argument('--jobs', default=1, type=lambda x: max(1, int(x)), metavar='N', help='The number of concurrent parsers to use.')
    parser.add_argument('--convert-UTF8', action='store_true', help='Not yet implemented. Only HTML entity references for now.')

    arguments = parser.parse_args()
    out_dir = arguments.output_dir
    if sha512sum(arguments.input) != OEDT_SHA512:
        raise RuntimeError("Checksum failure. This is not the right input file.")
    else:
        print("Correct checksum")

    try:
        offset_file = open(OFFSET_FILENAME, 'r')
    except:
        raise RuntimeError("Can't open offset file.")
    offsets = [
        int(l)
        for l in iter(offset_file.readline, '')
    ]

    try:
        os.makedirs(out_dir, exist_ok=True)
    except:
        raise RuntimeError("Can't create output directory")

    print("Decompressing...")

    fileset = {
        entry.name
        for entry in os.scandir(out_dir)
        if entry.is_file()
    }

    io_info = [
        OutputInfo("%d" % (b), "%d.json" % b, b, e)
        for b,e in zip(offsets, offsets[1:])
    ]

    files_needing_extraction = [
        info
        for info in io_info
        if (
            info.raw not in fileset and info.json not in fileset
        )
    ]

    count = 0
    for info in files_needing_extraction:
        count += 1
        sys.stdout.write('\r  %.1f%%' % (100 * count / len(files_needing_extraction)))
        try:
            file_output = open(os.path.join(out_dir, info.raw), 'wb')
        except:
            raise RuntimeError("Can't create output file.")

        file_output.write(decompress_block(arguments.input, info.begin, info.end))
        file_output.close()
    print("\rParsing...")

    fileset = {
        entry.name
        for entry in os.scandir(out_dir)
        if entry.is_file()
    }

    thread_args = list([
        (os.path.join(out_dir, info.raw), os.path.join(out_dir, info.json), info.begin, info.end)
        for info in io_info
        if (
            info.raw in fileset
        )
    ])

    start = time.time()
    count = 0
    with concurrent.futures.ProcessPoolExecutor(arguments.jobs) as ex:
        for info in ex.map(convert, thread_args):
            # print(info)
            os.remove(info[0])
            count += 1
            time_per_file = (time.time() - start) / count
            time_remaining = time_per_file * (len(thread_args) - count)
            sys.stdout.write('\r  %.1f%% Time Remaining: %d:%02d         ' % (100 * count / len(thread_args), time_remaining // 60, time_remaining % 60))

    print("Done.")


if __name__ == "__main__":
    main()
