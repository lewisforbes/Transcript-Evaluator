from re import sub
import re
from os import path
import os
import sys

from werpy import normalize
from jiwer import wer

# gets text content from a VTT or SRT file
# https://github.com/lewisforbes/VTT-to-TXT
def get_sub_contents(subtitle_fpath):
    with open(subtitle_fpath, "r", encoding='utf-8') as f:
        output = ""
        next = False
        for line in f:
            if next:
                if line=="\n":
                    next = False
                    continue
                line = sub("<[^>]*>", "", line) # remove tags
                output += line.replace("\n", "") + " "
                continue
            
            if "-->" in line:
                next = True


    # TODO move in loop
    # fix up output
    output = re.sub("\[.+?\]", "", output) # remove speaker/context tags
    output = re.sub("  +", " ", output) # remove multiple spaces
    return output

# calculates the word error rate (expressed as an accuracy) between two transcripts.
# gtrans: generated transcript
# ctrans: correct transcript
def get_accuracy(gtrans, ctrans):
    return 1 - wer(normalize(ctrans), normalize(gtrans))


# returns true iff a file is a subtitle file
def is_subtitle(fpath):
    return path.splitext(fpath)[1] in [".srt", ".vtt"]

# returns subset of os.listdir for which all subdirnames are numeric only when num_only=True
def list_video_dirs(data_dir, num_only):
    vid_dirs = [d for d in os.listdir(data_dir) if path.isdir(path.join(data_dir, d))]
    if len(vid_dirs)==0:
        error(f"there are no subfolders in '{data_dir}.")
    if not num_only:
        return [path.join(data_dir, vd) for vd in vid_dirs]
    
    output = []
    for d in vid_dirs:
        try:
            int(d)
            output.append(path.join(data_dir, d))
        except ValueError:
            continue
    return output

# returns true iff two file contents are different
def contents_different(p1, p2):
    if p1==p2: return False
    
    with open(p1, "r") as f1:
        with open(p2, "r") as f2:
            return f1.read()!=f2.read()
        

def error(msg):
    print(f"Error: {msg}\n")
    sys.exit()