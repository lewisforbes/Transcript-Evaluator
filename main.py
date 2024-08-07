from utils import *
import os
from os.path import join
import argparse
import csv
import metrics
from shutil import get_terminal_size

###########
# helpers #
###########
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
    p.add_argument("--metric", "-m", type=str, default="wer", help="metric to use in evaluation. Must be wer, rouge or bleu. Default is wer.")
    p.add_argument("--quiet", "-q", action='store_true', help="supresses warnings")

    args = p.parse_args()

    # validate --metric
    args.metric = args.metric.lower()
    if args.metric.startswith("rougel"): args.metric = "rougeL"+args.metric[6:] # format rougeL and rougeLsum
    if not metric_valid(args.metric):
        if args.metric=="rouge":
            print("Which ROUGE? Specify rougeL/rougeLsum or rouge1, rouge2 etc.")
        error("--metric/-m must be one of 'wer', 'bleu', 'rougeL', 'rougeLsum', 'rouge[1-9]'")

    Warning().quiet = args.quiet

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

# writes results file, prints summary table, gives info to user if output blank
def write_output(output, args):
    results_fpath = "results.csv"
    while True:
        try:
            with open(results_fpath, "w") as f:
                csv.writer(f, lineterminator="\n").writerows(output)
                break # while True
        except PermissionError:
            input("\nError: results.csv is open, close it and press enter to overwrite.\nAlternatively, press ctrl+C to quit.")

    ## SUMMARY TABLE ##
    if len(output)>1:
        # format metric
        if args.metric=="rougeL":
            fmetric = "ROUGE-L (sentence-level)"
        elif args.metric=="rougeLsum":
            fmetric = "ROUGE-L (summary-level)"
        else: # ROUGE-N and everything else
            fmetric = f"ROUGE-{args.metric[-1]}" if "rouge" in args.metric else args.metric.upper() 

        # print average summary
        if not args.quiet:
            print(f"\nAverage {fmetric} Accuracies...")
            max_len  = max([len(k) for k in scores_total])
            for s, data in scores_total.items():
                if data[1]==0:
                    print(f"{s}{' '*(4+max_len-len(s))}N/A")
                else: 
                    print(f"{s}{' '*(4+max_len-len(s))}{round(100*data[0]/data[1], 1)}%")

    ## NO INFO IN OUTPT ##
    if len(output)==1:
        print("\nNo media found. Refer to readme for data structure information.") 
    elif not args.quiet:
        s = "" if len(output)==2 else "s"
        print(f"\nFound {len(output)-1} media item{s}. See: {join(os.getcwd(),results_fpath)}.")

    # check if user might have put wrong folder
    # initiate this by moving `data_folder` to new dir `test` and run `python main.py -d test`
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
        print(f"But first try running: {cmd}")


########
# main #
########
if __name__=="__main__":
    # installation message 
    if len(sys.argv)==1:
        msg = "--- Installed correctly! ---"
        print(f"{'-'*len(msg)}\n{msg}\n{'-'*len(msg)}\n")
        try:
            tokens = ["this", "is", "a", "test"]
            corpus_bleu([[tokens]], [tokens])
        except TypeError:
            print("Warning: BLEU not available due to a problem with NLTK.")
            print("         Try run: `pip uninstall nltk -y` then `python main.py`.\n")


    args = mk_args()

    # {service: [sum of score, count of scores]}
    scores_total = {}
    for s in args.services: scores_total[s] = [0, 0]

    output = [["media folder"] + args.services] # init headers

    # make iterator    
    vid_dirs = list_video_dirs(args.data, args.numeric)
    if not args.quiet: # show progress bar
        vid_dirs = tqdm(vid_dirs, ncols=(min(110, get_terminal_size().columns)-2), ascii=" -") # ascii param to fix [?] char showing on windows terminal

    # go through each subfolder containing data
    for dirpath in vid_dirs:
        human_fpath, services = get_transcript_paths(dirpath, args)

        # check human and ai exist
        if not human_fpath or list(services.values())==["" for _ in services]:
            continue

        # calculate accuracy where applicable, create line for csv
        output_line = [path.basename(dirpath)]
        for s, ai_fpath in services.items():
            if ai_fpath=="": output_line.append("")
            else: 
                acc_score = metrics.get_accuracy(human_fpath, ai_fpath, args)
                if acc_score < 0.2: # arbitrary hard-coded value
                    warning(f"these appear completely different: '{human_fpath[len(args.data):]}' & '{ai_fpath[len(args.data):]}' (score {round(100*acc_score)}%)")
                
                # update scores_total
                current = scores_total[s]
                scores_total[s] = [current[0]+acc_score, current[1]+1]
                
                # add score to current output row
                output_line.append(acc_score)

        assert len(output_line)==len(output[0]), f"line in output wrong length: {len(output_line)}, {len(output[0])}"
        output.append(output_line) # add row to output csv

    Warning().show_warnings() # nothing if quiet
    write_output(output, args)