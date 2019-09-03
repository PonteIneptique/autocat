""" This scripts is meant as a tool to analyze which disambiguation can be learned
from POS only. This will generate a json file that can feed an automatic disambiguation tool.

It will also generates a list of lemma that cannot be disambiguated this way.
This means focus should happen on these specific lemma for disambiguation, because
this is real WSD.

The file format is a TSV containing lemmatized and pos-tagged texts
    where there is at least "lemma", "pos" and "Dis" in the header,
    where "Dis" holds the disambiguation index

    eg. (here, 4 spaces is equal to tab)
        token	lemma	pos	Dis.
        qui	qui	PROint	1
        est....
        celui...
        qui	qui	PROint	2
        a ....
        fait ...
        ca...
        ?...
"""

import glob
from autocat import detector
import json
import argparse


def run(prefix, category_key, lemma_key, files, disambiguation_key):
    if not files:
        raise Exception("No files found")

    def null_value(string):
        if string and string != "_":
            return True

    stats = detector.read_corpus(files,
                                 lemma_key=lemma_key, category_key=category_key, null_dis=null_value,
                                 disambiguation_key=disambiguation_key
                                 )
    dispatched = detector.dispatch(stats)

    print()
    print()
    print("--- Summary ---")
    print()

    total = 0
    auto = 0
    keys = sorted(dispatched.stats_per_dis_nb.keys())
    for nb in keys:
        details = dispatched.stats_per_dis_nb[nb]
        print("Lemma with {} different sublemma".format(nb))

        if nb == 1:
            auto += details["total"]
        else:
            auto += details["auto"]

        total += details["total"]

        print("--- Total: {}".format(details["total"]))
        print("--- Auto.: {}".format(details["auto"]))
        print("--- Auto%: {:.2f}".format(details["auto"]/details["total"]*100))

    print("Mixed")
    print("--- Total: {}".format(total))
    print("--- Auto.: {}".format(auto))
    print("--- Auto%: {:.2f}".format(auto/total*100))
    print("{} lemma with partial automatization possible".format(len(dispatched.partially_categorizable)))
    print("{} lemma with no automatization possible".format(len(dispatched.uncategorizable)))
    print("{} lemma with no secondary possible disambiguation".format(len(dispatched.one_disambiguation_only)))

    with open(prefix+category_key+".json", "w") as f:
        json.dump(dispatched.autodisambiguation, f)
    with open(prefix+"straight.json", "w") as f:
        json.dump(dispatched.one_disambiguation_only, f)
    with open(prefix+"needs.json", "w") as f:
        json.dump(list(set(
            dispatched.uncategorizable + list(dispatched.one_disambiguation_only.keys()) + \
            list(dispatched.autodisambiguation.keys())
        )), f)


def cli():
    parser = argparse.ArgumentParser(
        description="Parse a corpus to build autodisambiguation based on some"
                    "secondary information such as POS or Gender"
    )

    parser.add_argument("category_key",
                        help="Key in the TSV files identifies the category that needs to be scanned")
    parser.add_argument("files", nargs="+",
                        help="TSV files with headers")
    parser.add_argument("--lemma_key", dest="lemma_key", default="lemma",
                        help="Key in the TSV files identifies lemma")
    parser.add_argument("--dis_key", dest="disambiguation_key", default="Dis",
                        help="Key in the TSV files identifies the disambiguation index")
    parser.add_argument("--prefix", dest="prefix", default="./",
                        help="Prefix for the files")

    args = parser.parse_args().__dict__
    run(**args)
