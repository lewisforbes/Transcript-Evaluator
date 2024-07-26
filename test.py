from subprocess import run, PIPE, Popen
from sys import argv

# main tests fail if you run installation then main in same call
if "installation" in argv:
    installation_tests=True
else:
    installation_tests=False

def test(m="wer", s="service1 service2", c="human", extra= "", want_keyword=False, keyword="error"):
    cmd = f"python main.py -d {"data_folder"} -m {m} -s {s} -c {c} {extra}"
    p = run(cmd, capture_output=True, text=True, shell=True)
    if keyword.lower() in (p.stdout.lower() + p.stderr.lower()):
        if want_keyword:
            print("Passed")
        else:
            print(f"Failed: {cmd}")
    else:
        if want_keyword:
            print(f"Failed: {cmd}")
        else:
            print("Passed")

if installation_tests:
    print("INSTALLATION TESTS")
    run("pip uninstall -y -r requirements -q", capture_output=True, shell=True, text=True)

    p = Popen("python main.py", stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    stdout, stderr = p.communicate(input="no")
    if "Exiting" in stdout+stderr:
        print("Passed")
    else:
        print("Failed: installation decline")

    print("this will take a while...", flush=True, end=" ")
    process = Popen("python main.py", stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    stdout, stderr = process.communicate(input="yes")

    p = run("python main.py", capture_output=True, text=True, shell=True)
    if "installed correctly!" in p.stdout.lower():
        print("Passed")
    else:
        print("Failed: installation")

    if "BLEU not available due to a problem with NLTK".lower() in p.stdout.lower():
        print("Failed: good NLTK installation")
    else:
        print("Passed")

else:
    print("Include 'installation' in arguments to run installation tests.")
    print("\nMAIN TESTS")
    # every metric + --numeric test
    for m in ["wer", "rougeL", "rougeLsum", "bleu"]:
        test(m=m)

    for i in range(1,10):
        test(m=f"rouge{i}")

    # bad metrics
    test(m="rouge", want_keyword=True)
    test(m="rouge10", want_keyword=True)
    test(m="gkfbds", want_keyword=True)
    test(m="", want_keyword=True)


    # services + correct
    test(s="asdasdsa", keyword="No media found", want_keyword=True)
    test(s="service1", keyword="service2", want_keyword=False)
    test(s="human", c="service1")

    # numeric
    test(extra="-n", keyword="No media found", want_keyword=True)

    # quiet
    test(extra="-q", keyword=" ", want_keyword=False)     
    test(keyword=" ", want_keyword=True)