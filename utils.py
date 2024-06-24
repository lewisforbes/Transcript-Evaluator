from re import sub
from os import path
import os

from werpy import normalize
from nltk.translate.bleu_score import corpus_bleu

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
    return output


# calculates the bleu score between two transcripts.
# gtrans: generated transcript
# ctrans: correct transcript
def get_bleu_score(gtrans, ctrans, adjust=0.41):
    # tokenize transcript
    gtokens = normalize(gtrans).strip().split()
    ctokens = normalize(ctrans).strip().split()

    # calculate bleu score
    bleu = corpus_bleu([[ctokens]], [gtokens])

    # adjust score
    bleu = 1 - adjust + adjust*bleu # 1-((1-x)*a)

    return bleu

# returns true iff a file is a subtitle file
def is_subtitle(fpath):
    return path.splitext(fpath)[1] in [".srt", ".vtt"]

# returns subset of os.listdir for which all subdirnames are numeric only
def list_video_dirs(data_dir, num_only):
    vid_dirs = [d for d in os.listdir(data_dir) if path.isdir(path.join(data_dir, d))]
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
    with open(p1, "r") as f1:
        with open(p2, "r") as f2:
            return f1.read()!=f2.read()