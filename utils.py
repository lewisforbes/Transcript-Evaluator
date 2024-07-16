from re import sub, match
from os import path
import os
import sys

## SAFE IMPORTING ##
# `from utils import *` in other files
try:
    from jiwer import wer
    from jiwer.transformations import wer_standardize
    from nltk.translate.bleu_score import corpus_bleu
    from rouge_score import rouge_scorer
    from tqdm import tqdm
except ModuleNotFoundError:
    if "python3" in sys.orig_argv[0]:
        print("\nRunning with `python3` or `py` is known to sometimes not work on managed laptops. Try using `python`.")

    # ask user if they want to run pip install
    cmd = "pip install -r requirements -q"
    print(f"Installation incomplete.\nRun installation command `{cmd}`?", end="")
    if input(" [y/N] > ").lower().strip() in ["y", "yes"]:
        # yes
        print("Running command (may take a few minutes)...")
        os.system(cmd)
    print("Exiting.") # shown after installation command too
    sys.exit()
#####################


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
                return verify(sub(r" +", " ", f.read().replace("\n", " "))) # remove multiple spaces
            
            output = ""
            next = False
            for line in f:
                if next:
                    if line=="\n":
                        next = False
                        continue
                    line = sub(r"<[^>]*>", "", line) # remove <tags>
                    line = sub(r"\[[^\]]*\]", "", line) # remove [tags]
                    line = sub(r"  +", " ", line) # remove multiple spaces
                    output += line.replace("\n", "") + " "
                    continue
                
                if "-->" in line:
                    next = True

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

# validates args.metric
def metric_valid(m):
    if m in ["wer", "bleu", "rougeLsum"]: return True
    if len(m)==6 and match(r"rouge[1-9L]", m): return True # m is in [rougeL, rouge1, rouge2, ... , rouge9]
    return False

# show error message and end execution
def error(msg):
    print(f"Error: {msg}\n")
    sys.exit()

# shows warning message if not args.quiet
def warning(msg):
    if not Quiet.quiet: 
        print(f"Warning: {msg}")

# singleton class for --quiet to enable global var
# Quiet.quiet is set in main.mk_args() and accessed in utils.warning()
class Quiet:
    def __new__(cls):
        if cls._instance is None: # None when first called
            cls._instance = super(Quiet, cls).__new__(cls)
        return cls._instance