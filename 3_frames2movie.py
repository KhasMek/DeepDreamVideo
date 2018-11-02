#!/usr/bin/python

import argparse
import os
import os.path
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from shutil import which


def parse_args(print_help=False):
    argparser = argparse.ArgumentParser(prog='movie2frames')
    argparser.add_argument('imagedir', help='Directory of images that \
                           have been sent through DeepDream.', nargs='+')
    argparser.add_argument('source', help='Original video file.', nargs='+')
    argparser.add_argument('-e', '--encoder', default='ffmpeg',
                           help='select which encoder to use. \
                           (default: %(default)s)')
    argparser.add_argument('-o', '--outfile', help='name of final video file')
    argparser.add_argument('-t', '--type', default='jpg', help='image type to \
                           output. (default: %(default)s)',
                           choices=['jpg', 'png'])
    argparser.add_argument('-c', '--codec', default='libx264', help='codec to \
                           encode video with (ffmpeg only). \
                           (default: %(default)s)')
    args = argparser.parse_args()
    if print_help:
        return argparser.print_help()
    else:
        return args


def prepare_command(imagedir, source, encoder, file_type, outfile, codec):
    error = False
    cmd = []
    tmpvideo = tempfile.NamedTemporaryFile(suffix='.mp4')
    tmpaudio = tempfile.NamedTemporaryFile(suffix='.aac')
    if encoder == 'mplayer':
        if which('mplayer') and which('mencoder'):
            infiles = 'mf://{}/%08d.{}'.format(imagedir, file_type)
            bitrate = 'bitrate={}'.format(int(mplayer_get_bitrate(source)))
            fps = mplayer_get_fps(source)
            fps_string = 'fps={}:type={}'.format(fps, file_type)
            cmd_01 = [
                which('mencoder'),
                source,
                '-of', 'rawaudio',
                '-oac', 'mp3lame',
                '-ovc', 'copy',
                '-o', tmpaudio.name
            ]
            cmd.append(cmd_01)
            cmd_02 = [
                which('mencoder'),
                infiles,
                '-mf', fps_string,
                '-ovc', 'x264',
                '-x264encopts', bitrate,
                '-ofps', fps,
                '-audiofile', tmpaudio.name,
                '-oac', 'mp3lame',
                '-o', outfile
            ]
            cmd.append(cmd_02)
        else:
            error = True
    elif encoder == 'ffmpeg':
        if which('ffmpeg') and which('ffprobe'):
            infiles = '{}/%08d.{}'.format(imagedir, file_type)
            fps = ffmpeg_get_fps(source)
            fps_string = 'fps={},format=yuv420p'.format(fps)
            cmd_01 = [
                which('ffmpeg'),
                '-framerate', fps,
                '-i', infiles,
                '-c:v', codec,
                '-vf', fps_string,
                '-tune', 'fastdecode',
                '-tune', 'zerolatency',
                '-profile:v', 'baseline',
                tmpvideo.name,
                '-y'
            ]
            cmd.append(cmd_01)
            cmd_02 = [
                which('ffmpeg'),
                '-i', source,
                '-strict', '-2',
                tmpaudio.name,
                '-y'
            ]
            cmd.append(cmd_02)
            cmd_03 = [
                which('ffmpeg'),
                '-i', tmpaudio.name,
                '-i', tmpvideo.name,
                '-strict', '-2',
                '-c:v', 'copy',
                '-movflags', 'faststart',
                '-shortest',
                outfile
            ]
            cmd.append(cmd_03)
        else:
            error = True
    if error:
        print("ERROR! \"{}\" not found. Please make sure \
              it's in your $PATH".format(encoder))
        sys.exit(1)
    else:
        return cmd


def ffmpeg_get_fps(source):
    cmd = [
        which('ffprobe'),
        '-show_streams',
        '-select_streams', 'v',
        '-i', source
    ]
    r = str(subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode())
    raw_fps = [i for i in r.splitlines() if "r_frame_rate" in i]
    fps = raw_fps[0].rsplit('=', 1)[1]
    return fps


def remove_tmpfiles(tmpfiles):
    for tmpfile in tmpfiles:
        os.remove(tmpfile)


def mplayer_get_bitrate(source):
    cmd = [
        which('mplayer'),
        '-really-quiet',
        '-vo', 'null',
        '-ao', 'null',
        '-frames', '0',
        '-identify', source
    ]
    r = str(subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode())
    raw_bitrate = [i for i in r.splitlines() if "ID_VIDEO_BITRATE" in i]
    bitrate = int(raw_bitrate[0].rsplit('=', 1)[1])/1000
    return bitrate


def mplayer_get_fps(source):
    cmd = [
        which('mplayer'),
        '-really-quiet',
        '-vo', 'null',
        '-ao', 'null',
        '-frames', '0',
        '-identify', source
    ]
    r = str(subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode())
    raw_fps = [i for i in r.splitlines() if "ID_VIDEO_FPS" in i]
    fps = raw_fps[0].rsplit('=', 1)[1]
    return fps


def name_outfile(source):
    basename, extension = source.rsplit('.', 1)
    dreamname = 'deepdream-{}-{}.{}'.format(os.path.basename(basename),
                                            int(time.time()), extension)
    return dreamname


def main(imagedir, source, encoder, file_type, outfile, codec):
    if os.path.isfile(source) and os.path.isdir(imagedir):
        start_time = datetime.now()
        print(" START TIME: {}".format(start_time))
        cmd = prepare_command(imagedir, source, encoder, file_type, outfile, codec)
        for c in cmd:
            subprocess.run(c)
        end_time = datetime.now()
        print(" END TIME: {}".format(end_time))
        print(" TOOK {}".format(end_time - start_time))
    else:
        print(source)
        print("ERROR! imagedir or source file not found\n")
        parse_args(print_help=True)
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    source = os.path.abspath(args.source[0])
    imagedir = os.path.abspath(args.imagedir[0])
    if not args.outfile:
        outfile = name_outfile(source)
    main(imagedir, source, args.encoder, args.type, outfile, args.codec)
