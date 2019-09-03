import json
import abc
from typing import Dict, Optional, Tuple, Iterable, Any, List, Set


Default_lemma_key = "lemma"
Default_return_char = "?"
Default_join_string = "_"


class ProtoDisambiguator:

    known_tokens: Set[str] = abc.abstractproperty

    @abc.abstractmethod
    def disambiguate(self, tasks) -> Optional[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def from_file(cls, filepath, lemma_key=Default_lemma_key, **kwargs):
        raise NotImplementedError

    def disambiguate_rows(self, rows: Iterable[Dict[str, Any]]):
        for row in rows:
            yield self.disambiguate(row) or ""


class NeedsDisambiguation(ProtoDisambiguator):
    def __init__(self, categorizable: List[str], lemma_key: str = Default_lemma_key, return_char=Default_return_char):
        self.return_char = return_char
        self.categorizable = categorizable
        self.lemma_key = lemma_key
        self.known_tokens = set(categorizable)

    def disambiguate(self, tasks):
        lemma = tasks[self.lemma_key]
        if lemma in self.categorizable:
            return self.return_char

    @classmethod
    def from_file(cls, filepath, return_char=Default_return_char, lemma_key=Default_lemma_key):
        with open(filepath) as f:
            cats = json.load(f)
        return cls(return_char=return_char, categorizable=cats, lemma_key=lemma_key)


class CategoryAutodisambiguation(ProtoDisambiguator):
    def __init__(
            self,
            category_key: str,
            categorizable: Dict[str, Dict[str, str]],
            lemma_key: str = Default_lemma_key,
    ):
        self.category_key = category_key
        self.lemma_key = lemma_key
        self.categorizable: Dict[str, Dict[str, str]] = categorizable
        self.known_tokens = set(self.categorizable.keys())

    def disambiguate(self, tasks) -> Optional[Tuple[str, str]]:
        lemma = tasks[self.lemma_key]
        if lemma in self.categorizable:
            cat = tasks.get(self.category_key, None)
            return self.categorizable[lemma].get(cat, None)

    @classmethod
    def from_file(cls, filepath, category_key=None, lemma_key=Default_lemma_key):
        if not category_key:
            raise AssertionError("A CategoryDisambiguator should have a `category_key` parameter at loading time")
        with open(filepath) as f:
            cats = json.load(f)
        return cls(category_key=category_key, categorizable=cats, lemma_key=lemma_key)


class StraightAutodisambiguation(ProtoDisambiguator):
    def __init__(
            self,
            categorizable: Dict[str, str] = None,
            lemma_key: str = Default_lemma_key
    ):
        self.lemma_key = lemma_key
        self.categorizable: Dict[str, Dict[str, str]] = categorizable
        self.known_tokens = set(self.categorizable.keys())

    @classmethod
    def from_file(cls, filepath, lemma_key=Default_lemma_key, **kwargs):
        with open(filepath) as f:
            cats = json.load(f)
        return cls(categorizable=cats, lemma_key=lemma_key)

    def disambiguate(self, tasks):
        lemma = tasks[self.lemma_key]
        return self.categorizable.get(lemma, None)


class GroupAutodisambiguation(ProtoDisambiguator):
    def __init__(self, categorizers: Tuple[ProtoDisambiguator, ...], lemma_key: str = Default_lemma_key):
        self.categorizers = categorizers
        self.lemma_key = lemma_key

        self.known_tokens = set()
        for cat in self.categorizers:
            self.known_tokens.update(cat.known_tokens)

    def disambiguate(self, tasks):
        lemma = tasks[self.lemma_key]
        if lemma in self.known_tokens:
            for categorizer in self.categorizers:
                val = categorizer.disambiguate(tasks)
                if val:
                    return val
