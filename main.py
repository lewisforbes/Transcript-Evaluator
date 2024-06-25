from utils import *
import os
from os.path import join
import argparse
import csv

def mk_args():
    default_adjust = 1
    p = argparse.ArgumentParser()
    p.add_argument("--data", "-d", type=str, help="path of directory containing data", required=True)
    p.add_argument("--services", "-s", type=str, nargs="+", default=["verbit", "speechmatics", "adobe"], help="services to look for to evaluate")
    p.add_argument("--numeric", "-n", action='store_true', help="ignore folders which have letters in their names within main data folder")
    p.add_argument("--adjust", "-a", type=float, default=default_adjust, help="the adjust constant (see utils.get_bleu_score()).")
    args = p.parse_args()

    # validate services
    for i, s_i in enumerate(args.services):
        for j, s_j in enumerate(args.services):
            if (i!=j) and (s_i in s_j):
                error(f"service '{s_i}' is a substring or matches '{s_j}' which is not allowed. Ask Lewis to fix this.")
    
    if args.adjust>1 or args.adjust<0:
        p.error("adjust must be between 0 and 1")
    
    if args.adjust!=default_adjust: print(f"Using adjust={args.adjust}")
    return args

# returns filepaths of transcripts in directory `d`
# `human_fpath`: filepath of correct transcript
# `services` {service name: fpath}: filepath(s) of ai transcript(s)
def get_transcript_paths(d, args):
    # services within current directory and their filepaths
    services = {}
    for s in args.services: services[s] = ""

    # get transcipt filepaths
    human_fpath = None
    for fname in os.listdir(d):
        if is_subtitle(fname):
            # find human transcript
            if "human" in fname:
                # check for existing different file
                if human_fpath and contents_different(human_fpath, join(d, fname)): 
                    error(f"Both '{path.basename(human_fpath)}' and '{fname}' refer to human transcripts in '{d}' but are different.")
                human_fpath=join(d, fname)
            
            # find service transcript(s)
            for s in services:
                if s in fname:
                    # check for existing different file
                    if services[s]!="" and contents_different(services[s], join(d, fname)):
                        error(f"Both '{path.basename(services[s])}' and '{fname}' refer to {s} transcripts in '{d}' but are different.")
                    services[s] = join(d, fname)

                    # check for file named as human and service
                    if services[s]==human_fpath: error(f"ambiguous filename '{fname}'. Is it human or {s}?")

    # check all fpaths (vals) in services are unique
    for s_i, fp_i in services.items():
        if fp_i=="": continue
        for s_j, fp_j in services.items():
            if s_i!=s_j and fp_i==fp_j: # services different files same
                error(f"ambiguous file '{fp_i}'. Is it {s_i} or {s_j}?")

    return human_fpath, services

# returns the bleu score of a generated transcript
def score(correct_fpath, generated_fpath, args):
    # make transcripts
    ctrans = get_sub_contents(correct_fpath)
    gtrans = get_sub_contents(generated_fpath)

    # caluclate and return bleu
    return get_bleu_score(gtrans, ctrans, adjust=args.adjust)

if __name__=="__main__":
    args = mk_args()

    # {service: [sum of score, count of scores]}
    scores_total = {}
    for s in args.services: scores_total[s] = [0, 0]


    output = [["video folder"] + args.services] # init headers
    
    # go through each subfolder containing data
    for dirpath in list_video_dirs(args.data, args.numeric):
        human_fpath, services = get_transcript_paths(dirpath, args)

        # check human and ai exist
        if not human_fpath or list(services.values())==["" for _ in services]:
            continue

        # calculate bleu score where applicable, create line for csv
        output_line = [path.basename(dirpath)]
        for s, ai_fpath in services.items():
            if ai_fpath=="": output_line.append("")
            else: 
                acc_score = score(human_fpath, ai_fpath, args)
                if acc_score==0: print(f"Warning, following files appear completely different: '{human_fpath}' & '{ai_fpath}'.")
                
                # update scores_total
                current = scores_total[s]
                scores_total[s] = [current[0]+acc_score, current[1]+1]
                
                # add score current output row
                output_line.append(acc_score)

        assert len(output_line)==len(output[0]), f"line in output wrong length: {len(output_line)}, {len(output[0])}"
        output.append(output_line) # add row to output csv


    # write output
    while True:
        try:
            with open("results.csv", "w") as f:
                csv.writer(f, lineterminator="\n").writerows(output)
                break
        except PermissionError:
            input("\nError: results.csv is open, close it and press enter to overwrite.\nAlternatively, press ctrl+C to quit.")

    s = "" if len(output)==2 else "s"
    print(f"\nFinished. Found {len(output)-1} video{s}.")

    # print average summary
    print("\nAverage Accuracies...")
    max_len  = max([len(k) for k in scores_total])
    for s, data in scores_total.items():
        if data[1]==0:
            print(f"{s}{' '*(4+max_len-len(s))}N/A")
        else: 
            print(f"{s}{' '*(4+max_len-len(s))}{round(100*data[0]/data[1], 1)}%")