#!/usr/bin/python

import argparse
import os
import os.path
import progressbar
import subprocess
import sys

from datetime import datetime
from shutil import which, rmtree


def parse_args(print_help=False):
    argparser = argparse.ArgumentParser(prog='movie2frames')
    argparser.add_argument('source', help='file to prepare for use with \
                           DeepDreamVideo.', nargs='+')
    argparser.add_argument('-d', '--directory', default=os.getcwd(),
                           help='root working \
                           directory to use. (session default: %(default)s)')
    argparser.add_argument('-e', '--encoder', default='ffmpeg',
                           help='select which encoder to use. \
                           (default: %(default)s)',
                           choices=['ffmpeg', 'mplayer'])
    argparser.add_argument('-t', '--type', default='jpg', help='image type to \
                           output. (default: %(default)s)',
                           choices=['jpg', 'png'])
    args = argparser.parse_args()
    if print_help:
        return argparser.print_help()
    else:
        return args


def prepare_command(source, encoder, file_type, outdir):
    error = False
    cmd = []
    if encoder == 'mplayer':
        print("Support for mplayer is currently disabled, use ffpmpeg instead")
        sys.exit(1)
        if which('mplayer'):
            if file_type == 'png':
                mplayercmd = 'png:z=9:outdir={}'.format(outdir)
            else:
                mplayercmd = 'jpg:outdir={}'.format(outdir)
            cmd = [
                which('mplayer'),
                '-vo', mplayercmd,
                '-ao', 'null',
                source
            ]
        else:
            error = True
    elif encoder == 'ffmpeg':
        if which('ffmpeg'):
            outfiles = '{}/%08d.{}'.format(outdir, file_type)
            cmd = [
                which('ffmpeg'),
                '-i', source,
                '-f', 'image2',
                outfiles
            ]
        else:
            error = True
    if error:
        print("ERROR! \"{}\" not found. Please make sure \
              it's in your $PATH".format(encoder))
        sys.exit(1)
    else:
        return cmd


def pngcrush(outdir):
    if which('pngcrush'):
        for root, dirs, files in os.walk(outdir):
            print("Running pngcrush on files in \"{}\"".format(root))
            with progressbar.ProgressBar(max_value=len(files)) as bar:
                i = 0
                for file in files:
                    i += 1
                    fpath = '{}/{}'.format(root, file)
                    cmd = [
                        which('pngcrush'),
                        '-ow',
                        '-m',
                        '115',
                        fpath
                    ]
                    subprocess.run(cmd, stderr=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL)
                    bar.update(i)
    else:
        print("ERROR! pngcrush is not installed, skipping...")


def prepare_outdir(directory):
    directory = '{}/source_frames'.format(os.path.abspath(directory))
    if os.path.exists(directory) and os.path.isdir(directory):
        q = input("Overwrite existing directory {}? [y/N] ".format(directory))
        if q in ['y', 'Y', 'yes']:
            rmtree(directory)
        else:
            print("Directory exists, exiting...")
            sys.exit(1)
    os.mkdir(directory)
    return directory


def main(source, encoder, file_type, outdir):
    cmd = prepare_command(source, encoder, file_type, outdir)
    if os.path.isfile(source):
        start_time = datetime.now()
        print(" START TIME: {}".format(start_time))
        subprocess.run(cmd)
        if args.type == 'png':
            pngcrush(outdir)
        end_time = datetime.now()
        print(" END TIME: {}".format(end_time))
        print(" TOOK {}".format(end_time - start_time))
    else:
        print(source)
        print("ERROR! File not found\n")
        parse_args(print_help=True)
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    source = os.path.abspath(args.source[0])
    outdir = prepare_outdir(args.directory)
    main(source, args.encoder, args.type, outdir)
