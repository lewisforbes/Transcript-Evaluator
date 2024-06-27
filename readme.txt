## Overview

This program automates the accuracy testing of transcripts, given a
human-written correct transcript. It uses [Word Error
Rate](en.wikipedia.org/wiki/Word_error_rate), as this was found
to be a good predictor of human accuracy ratings for the same task. The
program's intended use is to compare between services, not give precise
accuracy scores to transcripts.


## Installation

1.  Download from github.com/lewisforbes/Transcript-Evaluator/archive/refs/heads/main.zip
    and unzip, or clone repo. Open terminal in directory.
2.  Install dependencies: `pip install -r requirements`.
3.  Verify installation: `python main.py`. If you get a NumPy error, run
    `pip uninstall numpy` **twice** and go to step 2.
4.  Run example command:
    `python main.py --data data_folder --service service1 service2`.


## Data Structure

The program relies on a data structured in a specific way to work.

    data_folder
    ├───video1
    │       this_is_the_human_transcript.srt
    │       subtitles_from_service1.vtt
    │       random_file.pdf
    │
    ├───video2
    │       human_transcript.vtt
    │   service1_subs.srt
    │   service2.srt
    │
    ...

Video folders (`video1`, `video2` here) can have any name.

Human transcript files must contain "human" in their filename.

Service (AI) transcript files must contain the service name in the
filename.


## Command Structure

An example command is:
`python main.py --data data_folder --services service1 service2`.

Where...

-   `--data <path>` is path to the folder containing data.
-   `--services <s1> <s2> ...` are the names of the services present.

Other flags:

-   `--numeric` ignores folders within the `--data` folder that have
    non-numeric characters in their names.
-   `--help` shows help information.

## Output

After running, the file results.csv is created or
overwritten. After installation step 4 it looks like this:

  media folder   service1             service2
  -------------- -------------------- ------------------
  video1         0.9704595185995624
  video2         0.9604261796042618   0.95662100456621


------------------------------------------------------------------------


### Attribution

Subtitles in data_folder/video1 by The University of
Edinburgh: www.youtube.com/watch?v=93Z48ALaBSQ.

Subtitles in data_folder/video2 by The University of
Edinburgh: www.youtube.com/watch?v=nq80hb4-klw.

Downloaded using Views4You:
www.views4you.com/tools/youtube-subtitles-downloader/.
