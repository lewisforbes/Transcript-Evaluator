from re import sub
from os import path
import os
import sys

# for get_accuracy()
from werpy import normalize
from jiwer import wer

# gets text content from a VTT or SRT file or return TXT body if applicable
# https://github.com/lewisforbes/VTT-to-TXT
def get_sub_contents(subtitle_fpath):
    # raises error if contents empty
    def verify(contents):
        if contents.strip()=="":
            error(f"'{subtitle_fpath}' is empty.")
        else:
            return contents

    with open(subtitle_fpath, "r", encoding='utf-8') as f:
        # return full body of text file
        if path.splitext(subtitle_fpath)[1]==".txt":
            return verify(sub(" +", " ", f.read().replace("\n", " "))) # remove multiple spaces
        
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
    output = sub("\[.+?\]", "", output) # remove speaker/context tags
    output = sub("  +", " ", output) # remove multiple spaces
    return verify(output)

# returns true iff two file contents are different
def contents_different(p1, p2):
    if p1==p2: 
        return False
    else:
        return get_sub_contents(p1)!=get_sub_contents(p2)

# returns true iff a file is a subtitle file (text files included)
def is_subtitle(fpath):
    return path.splitext(fpath)[1] in [".txt", ".srt", ".vtt"]

# returns subset of os.listdir for which all subdirnames are numeric only when num_only=True
def list_video_dirs(data_dir, num_only):
    vid_dirs = [d for d in os.listdir(data_dir) if path.isdir(path.join(data_dir, d))]
    if len(vid_dirs)==0:
        error(f"there are no subfolders in '{data_dir}'.")
    
    # non-numeric dirnames
    if not num_only:
        return [path.join(data_dir, vd) for vd in vid_dirs]
    
    # numeric dirnames
    output = []
    for d in vid_dirs:
        try:
            int(d)
            output.append(path.join(data_dir, d))
        except ValueError:
            continue
    return output

# show error message and end execution
def error(msg):
    print(f"Error: {msg}\n")
    sys.exit()