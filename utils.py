from re import sub
from os import path
import os
import sys

# gets text content from a VTT or SRT file or return TXT body if applicable
# https://github.com/lewisforbes/VTT-to-TXT
# this function looks conufusing but it's just a wrapper for _get_sub_contents()
# verify() is just assert contents!=""
def get_sub_contents(subtitle_fpath):
    # main function. used to try both encodings
    def _get_sub_contents(subtitle_fpath, encoding):
        # raises error if contents empty, otherwise returns contents
        def verify(contents):
            if contents.strip()=="":
                error(f"'{subtitle_fpath}' is empty.")
            else:
                return contents


        with open(subtitle_fpath, "r", encoding=encoding) as f:
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

    # utf-8 can lead to error http://bit.ly/3Wjd479
    # latin-1 can't decode some characters (such as —) but doesn't throw error 
    try:
        return _get_sub_contents(subtitle_fpath, "utf-8")
    except UnicodeDecodeError:
        warning(f"using latin-1 encoding for {subtitle_fpath}. Accuracy scores may be lower they should be for this file.")
        return _get_sub_contents(subtitle_fpath, "latin-1")

# returns true iff two file contents are different
def contents_different(p1, p2):
    if p1==p2: 
        return False
    else:
        return get_sub_contents(p1)!=get_sub_contents(p2)

# returns true iff a file is a subtitle or text file
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

# shows warning message if not args.quiet
def warning(msg):
    if not Quiet.quiet: 
        print(f"Warning: {msg}")

# singleton class for --quiet
# Quiet.quiet is set in main.mk_args() and accessed in utils.warning()
class Quiet:
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Quiet, cls).__new__(cls)
        return cls._instance