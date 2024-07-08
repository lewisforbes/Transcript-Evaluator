from utils import *
import os
from os.path import join
import argparse
import csv

# gold standard transcript identifier in filename.
# MUST BE LOWERCASE: filenames all .lower()'d in comparisons
# HUMAN = "human"

# construct parser, return arguments
def mk_args():
    # make parser
    p = argparse.ArgumentParser()
    if os.path.exists("data_folder"):
        p.epilog = "Example command: python main.py --data data_folder --service exampleservice anotherservice"
        
    p.add_argument("--data", "-d", type=str, help="path of directory containing data", required=True)
    p.add_argument("--services", "-s", type=str, nargs="+", default=["verbit", "speechmatics", "adobe"], help="services to look for to evaluate")
    p.add_argument("--numeric", "-n", action='store_true', help="ignore folders which have letters in their names within main data folder")
    p.add_argument("--correct", "-c", type=str, default="human", help="keyword used to identify human (correct/gold standard) transcript")

    args = p.parse_args()

    # validate --data
    if not os.path.exists(args.data): error(f"path '{args.data}' does not exist.")
    if not os.path.isdir(args.data): error(f"path '{args.data}' is not a directory.")

    # validate services
    args.services = [s.lower() for s in args.services] # for comparison
    # args.correct is substring of or equals a service
    if True in [(args.correct in s) for s in args.services]:
        if args.correct in args.services:
            error(f'"{args.correct}" is invalid service name. This is used to identify the human-written transcript.')
        else: # human is substring of some service
            error(f"service {[s for s in args.services if args.correct in s][0]} contains '{args.correct}' which is not allowed. This transcript would be recognised as human-written.")
    
    # service1 substring of service2 or of args.correct
    for i, s_i in enumerate(args.services + [args.correct]):
        for j, s_j in enumerate(args.services + [args.correct]):
            if (i!=j) and (s_i in s_j):
                error(f"service '{s_i}' is a substring or matches '{s_j}' which is not allowed.")

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
        fname = fname.lower()
        if is_subtitle(fname):
            # find human transcript
            if args.correct in fname:
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


# returns the accuracy of a generated transcript
def get_accuracy(correct_fpath, generated_fpath):
    # make transcripts
    ctrans = get_sub_contents(correct_fpath)
    gtrans = get_sub_contents(generated_fpath)

    # caluclate and return wer (expressed as accuracy)
    return 1 - min(1, wer(normalize(ctrans), normalize(gtrans))) # wer>1 possible (https://w.wiki/_sXTY)


# ## BLEU ##
# from nltk.translate.bleu_score import corpus_bleu
# def get_accuracy(correct_fpath, generated_fpath):
#     try: args.temp
#     except:
#         print("Warning: using BLEU")
#         args.temp = None
#     # make transcripts
#     ctrans = get_sub_contents(correct_fpath)
#     gtrans = get_sub_contents(generated_fpath)

#     ctokens = ctrans.strip().split()
#     gtokens = gtrans.strip().split()

#     return corpus_bleu([[ctokens]], [gtokens])

# ## ROUGE ##
# from rouge_score import rouge_scorer
# def get_accuracy(correct_fpath, generated_fpath):
#     try: args.temp
#     except:
#         print("Warning: using ROUGE")
#         args.temp = None


#     # make transcripts
#     ctrans = get_sub_contents(correct_fpath)
#     gtrans = get_sub_contents(generated_fpath)

#     scorer = rouge_scorer.RougeScorer(['rouge4'], use_stemmer=True)
#     scores = scorer.score(ctrans, gtrans)
#     return scores['rouge4'].fmeasure


if __name__=="__main__":
    if len(sys.argv)==1:
        msg = "--- Installed correctly! ---"
        print("-"*len(msg))
        print(msg)
        print("-"*len(msg), "\n")

    args = mk_args()

    # {service: [sum of score, count of scores]}
    scores_total = {}
    for s in args.services: scores_total[s] = [0, 0]


    output = [["media folder"] + args.services] # init headers
    
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
                acc_score = get_accuracy(human_fpath, ai_fpath)
                if acc_score<0.3: print(f"Warning, following files appear completely different: '{human_fpath}' & '{ai_fpath}'.")
                
                # update scores_total
                current = scores_total[s]
                scores_total[s] = [current[0]+acc_score, current[1]+1]
                
                # add score current output row
                output_line.append(acc_score)

        assert len(output_line)==len(output[0]), f"line in output wrong length: {len(output_line)}, {len(output[0])}"
        output.append(output_line) # add row to output csv


    # write output
    results_fpath = "results.csv"
    while True:
        try:
            with open(results_fpath, "w") as f:
                csv.writer(f, lineterminator="\n").writerows(output)
                break
        except PermissionError:
            input("\nError: results.csv is open, close it and press enter to overwrite.\nAlternatively, press ctrl+C to quit.")

    if len(output)==1:
        print("\nNo media found. Refer to readme for data structure information.") 
    else:
        s = "" if len(output)==2 else "s"
        print(f"\nFound {len(output)-1} media item{s}. See: {join(os.getcwd(),results_fpath)}.")

    if len(output)>1:
        # print average summary
        print("\nAverage Accuracies...")
        max_len  = max([len(k) for k in scores_total])
        for s, data in scores_total.items():
            if data[1]==0:
                print(f"{s}{' '*(4+max_len-len(s))}N/A")
            else: 
                print(f"{s}{' '*(4+max_len-len(s))}{round(100*data[0]/data[1], 1)}%")

    # check if user might have put wrong folder
    if len(output)==1 and len(list_video_dirs(args.data, num_only=False))==1:
        cmd = "python"
        data_next = False
        for a in sys.argv:
            if data_next:
                subdir = os.listdir(args.data)[0]
                subdir = f'"{subdir}"' if " " in subdir else subdir
                cmd += " " + join(args.data, subdir)
                data_next=False
            else:
                cmd += " " + a
                if a in ["--data", "-d"]:
                    data_next=True
        print(f"But first try running: {cmd}\n")
