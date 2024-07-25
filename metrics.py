# uses other libraries to perform evaluations
# to add another metric called "example":
#   1. write function: example_accuracy(correct_transcript, generated_transcript) -> accuracy as a decimal between 0 and 1
#   2. update utils.metric_valid()
#   3. update --metric information in main.mk_args() [one of the p.add_argument() linel]
#   4. update error message shown from main.mk_args when incorrect metric is used.
#   5. update readme

from utils import *

# wrapper. directs to correct metric function based on args.metric
def get_accuracy(correct_fpath, generated_fpath, args):
    # make transcripts
    ctrans = get_sub_contents(correct_fpath)
    gtrans = get_sub_contents(generated_fpath)

    # create and evaluate correct function
    if "rouge" in args.metric:
        return eval(f"rouge_accuracy(ctrans, gtrans, '{args.metric}')")
    else:
        return eval(f"{args.metric}_accuracy(ctrans, gtrans)")


####################
# accuracy scorers #
####################

# returns 1-WER
def wer_accuracy(ctrans, gtrans):
    # standardise transcripts and calculate wer score
    wer_score = wer(reference=ctrans, hypothesis=gtrans, 
                          reference_transform=wer_standardize,
                          hypothesis_transform=wer_standardize)

    # caluclate and return wer (expressed as accuracy)
    return 1 - min(1, wer_score) # wer>1 possible (https://w.wiki/_sXTY)

# returns BLEU score
def bleu_accuracy(ctrans, gtrans):
    ctokens = ctrans.strip().split()
    gtokens = gtrans.strip().split()

    try:
        return corpus_bleu([[ctokens]], [gtokens])
    except TypeError:
        print("\n\nError: NLTK not working. Try run `pip uninstall nltk -y` then `python main.py`.")
    input("Press enter to see the error...")
    corpus_bleu([[ctokens]], [gtokens]) # show full error
    error("Something went wrong when calculating the BLEU score.") # just in case


# returns ROUGE score
def rouge_accuracy(ctrans, gtrans, rouge_type):
    scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=True)
    scores = scorer.score(ctrans, gtrans)
    return scores[rouge_type].fmeasure