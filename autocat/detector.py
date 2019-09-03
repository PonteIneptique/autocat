import csv
from collections import Counter, defaultdict, namedtuple

from typing import Dict, Counter as CounterT, Callable, Union, List


def default_null_dis(string):
    if string and string != "_":
        return True
    return False


def read_corpus(
        files,
        lemma_key: str = "lemma",
        category_key: str = "pos",
        disambiguation_key: str = "Dis",
        null_dis: Callable[[str], bool] = default_null_dis
) -> Dict[str, Dict[str, CounterT[str]]]:
    stats = defaultdict(lambda: defaultdict(Counter))
    for file in files:
        with open(file) as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                disambiguation_index = row[disambiguation_key]
                if null_dis(disambiguation_index):
                    stats[row[lemma_key]][disambiguation_index][row[category_key]] += 1
    return stats


def stats_dict() -> Dict[str, Union[int, List]]:
    """ Function used to generate new dict entry for default dict
    """
    return {
        "total": 0,
        "auto": 0,
        "lemma": []
    }


Dispatched = namedtuple("Dispatched", [
    "stats_per_dis_nb", "partially_categorizable", "uncategorizable",
    "one_disambiguation_only", "autodisambiguation"
])


def dispatch(stats: Dict[str, Dict[str, Dict[str, int]]], limit_counter: int = 1):
    """ Based on a dictionary of counters

    :param stats: Dictionary of lemma to disambiguate with a dictionary of index below, themselves
                    holding each CATEGORY it has been found with and their count
                    eg {"qui": {"1": {"ADV": 1, "PROrel": 50}, "2" {"PROint": 87}}}
    :param limit_counter: Limit at which we assume the presence of a Category is an error
    :return:
    """
    stats_per_dis_nb = defaultdict(stats_dict)
    partialy_categorizable = []
    uncategorizale = []
    one_disambiguation_only = {}
    autodisambiguation = {}

    for lemma, sublemma in stats.items():
        cats = []
        for index, counter in sublemma.items():
            # Check that we have multiple categories
            if len(counter) > 1:
                # We keep only POS which have at least one presence, to filter out errors
                #   Note that we could filter it based on a ratio to take into account those errors
                count_pos = [POS for POS, count in counter.items() if count > limit_counter]

                # If we have at least one categories that appears more than the arbitrary limit
                if len(count_pos):
                    cats.append(count_pos)
                # If not, each categories happens only below the limit
                else:
                    continue
            else:
                # Some might only have POS with 1 occurences EVERYWHERE
                cats.append(list(counter.keys()))

        stats_per_dis_nb[len(sublemma)]["total"] += 1
        stats_per_dis_nb[len(sublemma)]["lemma"].append(lemma)

        # If we have more than one category
        if len(cats) > 1:
            cats_simplified = [el for li in cats for el in li]
            cats_set = list(set(cats_simplified))

            # Set is unordered... So it can shift things
            cats_simplified = sorted(cats_simplified)
            cats_set = sorted(cats_set)

            # if the list is equal to the set
            #  this means all variations are dispatched based on POS
            #  and are not based on meaning
            if cats_simplified == cats_set:
                stats_per_dis_nb[len(sublemma)]["auto"] += 1
                autodisambiguation[lemma] = {
                    pos: index
                    for index, counter in sublemma.items()
                    for pos, pos_count in counter.items()
                    if pos_count > limit_counter
                }

                if len(autodisambiguation[lemma]) == 0:
                    only_one = True
                    possible = {}
                    for index, counter in sublemma.items():
                        if len(counter) > 1:
                            only_one = False
                            break
                        else:
                            for pos, pos_count in counter.items():
                                possible[pos] = index
                                if not pos_count <= limit_counter:
                                    only_one = False
                                    break

                    if only_one:
                        autodisambiguation[lemma] = possible
                    else:
                        del autodisambiguation[lemma]
                        uncategorizale.append(lemma)

            # We have different categories in at least one sublemma
            elif len(cats_set) != 1:
                partialy_categorizable.append({"lemma": lemma, "sub": sublemma})
                autodisambiguation[lemma] = {
                    pos: index
                    for index, counter in sublemma.items()
                    for pos, pos_count in counter.items()
                    if pos_count > limit_counter and cats_simplified.count(pos) == 1
                }
            else:
                uncategorizale.append(lemma)

            # Check up that a dict has not been left empty
            if lemma in autodisambiguation and len(autodisambiguation[lemma]) == 0:
                print(lemma, sublemma)
        else:
            if len(sublemma.keys()) > 1:
                uncategorizale.append(lemma)
            else:
                one_disambiguation_only[lemma] = list(sublemma.keys())[0]
    return Dispatched(
        stats_per_dis_nb, partialy_categorizable, uncategorizale,
        one_disambiguation_only, autodisambiguation
    )
