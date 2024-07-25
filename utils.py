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
    cmd = "pip install -q -r requirements --no-warn-script-location"
    print(f"Installation incomplete.\nRun installation command `{cmd}`?", end="")
    if input(" [y/N] > ").lower().strip() in ["y", "yes"]:
        # yes
        print("\tRunning command (may take a few minutes)")
        os.system(cmd)

        # COMMENT OUT IF ISSUES! temporary fix to deal with corpus_bleu being broken in NLTK==3.8.1
        try:
            from nltk.translate.bleu_score import corpus_bleu
            tokens = ["this", "is", "a", "test"]
            corpus_bleu([[tokens]], [tokens])
        except ModuleNotFoundError: 
            pass # nltk didn't install
        except TypeError:
            print("Installing most current version of NLTK...")
            print("\tUninstalling NLTK")
            os.system("pip uninstall -y -q nltk")
            cmd = "pip install --no-warn-script-location -q git+https://github.com/nltk/nltk.git"
            print(f"\tRunning: `{cmd}`")
            os.system(cmd)
        # end temporary fix

        print("Installation command complete.", flush=True)
    else:
        print("Rerun and enter 'yes' to run installation command.")
        print("Exiting.", flush=True)
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
                    line = line.replace("\n", "") + " " # remove newlines
                    output += line
                    continue
                
                if "-->" in line:
                    next = True

        output = sub(r" +", " ", output) # remove multiple spaces
        return verify(output)

    # utf-8 can lead to error http://bit.ly/3Wjd479
    # latin-1 can't decode some characters (such as —) but doesn't throw error 
    try:
        return _get_sub_contents(subtitle_fpath, "utf-8")
    except UnicodeDecodeError:
        warning(f"using latin-1 encoding for '{subtitle_fpath}'. Accuracy scores may be lower they should be for this file.")
        return _get_sub_contents(subtitle_fpath, "latin-1")

# returns true iff two file contents are different
def contents_different(p1, p2):
    if p1==p2: 
        return False
    else:
        return get_sub_contents(p1)!=get_sub_contents(p2)

# returns true iff a file is a subtitle or text file
def is_subtitle(fpath):
    return path.splitext(fpath)[1].lower() in [".txt", ".srt", ".vtt"] # .lower() since some file extensions are all caps

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


# used to store and then display warnings throughout execution
# pointless wrapper bc it looks nicer
def warning(msg): Warning().warning(msg)
# actual class
class Warning:
    _instance=None
    def __new__(cls): # singleton
        if cls._instance is None:
            cls._instance = super(Warning, cls).__new__(cls)

            # attribute init
            cls._instance.warnings = []
            cls._instance.quiet = None # args.quiet

        return cls._instance

    # add warning to be shown later
    def warning(self, msg):
        if not self.quiet:
            msg = msg.strip()
            self.warnings.append(msg[0].upper() + msg[1:])
    
    # print warnings to console
    def show_warnings(self):
        if (not self.quiet) and (len(self.warnings)>=1):
            print("\nWarnings during execution:")
            for w in self.warnings:
                print(f"- {w}")
