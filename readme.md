### Attribution
Subtitles in [video1](data_folder/video1) by [The University of Edinburgh](https://www.youtube.com/watch?v=93Z48ALaBSQ). \
Subtitles in [video2](data_folder/video2) by [The University of Edinburgh](https://www.youtube.com/watch?v=nq80hb4-klw). \
Downloaded using [Views4You](https://views4you.com/tools/youtube-subtitles-downloader/).


## Overview
This program automates the accuracy testing of transcripts, given a human-written correct transcript. 
It uses [BLEU score](https://en.wikipedia.org/wiki/BLEU) as a baseline, and applies a positive weighting based on experiments. See [`utils.get_bleu_score()`](/utils.py) for algorithm details.
The program's intended use is to compare between services, not give precise accuracy scores to transcripts.

## Data Structure
The program relies on a data structured in a specific way to work.

```
data_folder
├───video1
│       this_is_the_human_transcript.srt
│       subtitles_from_exampleservice.vtt
│       random_file.pdf
│
├───video2
│       human_transcript.vtt
│	exampleservice_subs.srt
│	anotherservice.srt
│
...
```

Video folders (`video1`, `video2` here) can have any name.

Human transcript files must contain "human" in their filename.

Service (AI) transcript files must contain the service name in the filename.


## Command Structure
An example command is: `python main.py --data data_folder --services exampleservice anotherservice`.

Where...

- `--data <path>` is path to the folder containing data.
- `--services <s1> <s2> ...` are the names of the services present.

Other flags:

- `--numeric` ignores folders within the `--data` folder that have non-numeric characters in their names. 
- `--help` shows help information.



## Output

After running, the file [results.csv](/results.csv) is created or overwritten. It looks like this:

| video folder | exampleservice     | anotherservice     |
|--------------|--------------------|--------------------|
| video1       | 0.9270238931830127 |                    |
| video2       | 0.9085649807373941 | 0.8952361542394177 |
