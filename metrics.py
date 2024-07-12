from utils import get_sub_contents
import sys
try:
    from jiwer import wer
    from jiwer.transformations import wer_standardize
    from nltk.translate.bleu_score import corpus_bleu
    from rouge_score import rouge_scorer
except ModuleNotFoundError:
    if "python3" in sys.orig_argv[0]:
        print("\nRunning with `python3` or `py` is known to sometimes not work on managed laptops. Use `python`.")
    print("Installation incomplete. Run: pip install -r requirements")
    sys.exit()


# wrapper. directs to correct metric function based on args.metric
def get_accuracy(correct_fpath, generated_fpath, args):
    # make transcripts
    ctrans = get_sub_contents(correct_fpath)
    gtrans = get_sub_contents(generated_fpath)

    # create and evaluate correct function
    return eval(f"{args.metric}_accuracy(ctrans, gtrans)")


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

    return corpus_bleu([[ctokens]], [gtokens])

# returns ROUGE score
def rouge_accuracy(ctrans, gtrans):
    scorer = rouge_scorer.RougeScorer(['rouge4'], use_stemmer=True)
    scores = scorer.score(ctrans, gtrans)
    return scores['rouge4'].fmeasure