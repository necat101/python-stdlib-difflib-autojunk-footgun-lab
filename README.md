# python-stdlib-difflib-autojunk-footgun-lab

A small, deterministic Python standard-library correctness lab for `difflib.SequenceMatcher`, focusing on the default `autojunk` heuristic, the 200-element activation boundary, popularity state, argument-order sensitivity, matching blocks, opcodes, `get_close_matches()`, and the gap between fuzzy string similarity and validated machine-learning / record-linkage.

No external dependencies. No downloads. No training. No embeddings.

## What this repository tests

- `SequenceMatcher` API availability and `autojunk` parameter presence
- Identical short sequences: ratio 1.0 regardless of `autojunk`
- Empty sequence identity: empty-empty = 1.0, empty-nonempty = 0.0
- Order sensitivity: e.g. `"tide"` vs `"diet"` – ratio differs by argument order (local observation in CPython 3.12)
- Autojunk length boundary: 199-element repetitive second sequence does not activate popularity filtering; 200-element sequence with a token appearing 4 times (3 duplicates, 1.5%) does
- Strict >1% popularity threshold: 3 occurrences at length 200 (2 duplicates = exactly 1.0%) does NOT trigger; 4 occurrences (3 duplicates = 1.5%) DOES trigger
- Autojunk true vs false on long repetition: `["A"] + ["x"]*199` vs `["x"]*199 + ["A"]` – ratio changes materially
- Second-sequence popularity direction: popularity analysis is tied to the second sequence (`b`); reversing arguments can change the score
- Custom `isjunk`: explicit junk tokens are represented in `bjunk`
- Matching blocks: terminal zero-size dummy block at `(len(a), len(b))`
- Opcodes: `get_opcodes()` reconstructs the target sequence exactly
- Quick-ratio upper bounds: `quick_ratio()` and `real_quick_ratio()` ≥ `ratio()`
- `set_seq2()` reuse: fresh matchers and `set_seq1()`/`set_seq2()` reuse produce identical scores
- `get_close_matches()`: cutoff filtering, underlying `SequenceMatcher` ratios recorded separately
- Tiny record-linkage demo: arbitrary threshold on directional-mean scores – explicitly NOT ML, no precision/recall/accuracy/F1, no training
- Autojunk candidate ranking flip: deterministic query with a shifted repetitive candidate vs a mixed candidate – ranking can change with `autojunk=True/False` (local observation only, NOT a retrieval benchmark)
- No-global-claim marker: explicit disclaimers

## What WTFPython is

[WTFPython](https://github.com/satwikkansal/wtfpython) is a collection of "surprising snippets" in Python – short code examples that behave in ways that may surprise readers familiar with other languages or with a naïve mental model of Python. It is intended as an educational / entertainment resource about Python implementation quirks, edge cases, and traps.

It is NOT a machine-learning dataset, a bug tracker, or a claim that Python is unusable.

## What HN commenters said

This section summarizes sentiments from Hacker News thread [37281692](https://news.ycombinator.com/item?id=37281692) ("WTFPython: Exploring and understanding Python through surprising snippets").

Readers found WTFPython entertaining and educational. Several commenters said the examples resembled traps they had encountered in production or legacy projects, including mixed Python 2 / Python 3 codebases, and that people not well-versed in Python are often unaware of these gotchas.

Commenter 8589934591 (the author of the "production / legacy" observation) argued that type hints, testing, and tooling are important for long-lived Python projects, and mentioned Go as an alternative that "handles all of this automatically", with good results for small-to-medium projects in their experience. Other commenters pushed back: one commenter (oivey) said type hints / static typing would not prevent many of the quirks shown, which were due to "leaky compiler weirdness in CPython"; another (globular-toast) cited evidence suggesting typing is not the leading cause of bugs in Python (~1% type-related in a GitHub issue survey they recalled), and that rigorous typing may be "mostly a nerd snipe". The original commenter clarified that type hints were meant as a general boon for legacy projects outside the WTFPython repo specifically, and that their beliefs stemmed from local job-market experience rather than universal empirical evidence.

One commenter, kristianp, specifically singled out `difflib.SequenceMatcher` and its default `autojunk` behavior. They observed that despite passing `isjunk=None`, "the matcher will start classifying characters as junk once the b parameter is more than 200 characters long", and that "unless you read the docs carefully, your matcher will start not matching anything longer than a few characters once the input gets longer than a few sentences", with the fix being `autojunk=False`. That commenter speculated that "Its like the original writer of this component wrote the matcher for a specific application (DNA matching?) and left in the heuristic even though it isn't applicable to general use" – this DNA-matching explanation is **speculation by the commenter, not established library history**. The commenter also suggested backwards compatibility was the reason the heuristic remains enabled by default ("it still defaults to true, to keep backwards compat, and to confuse people").

Some commenters criticized Python's accumulated warts, with one (Pannoniae) arguing that for greenfield projects that aren't small throwaway projects, "using Python is not necessarily a very good idea" – a claim other commenters (stevesimmons, nerdponx) strongly disputed as an unjustified leap, arguing that every language has problems.

Other commenters defended Python as enjoyable and ergonomic despite its warts. globular-toast wrote: "Use it for a while and you'll understand why. It's a joy to use. That is successful despite its warts just goes to show how nice it is compared to other languages."

Arguments in the thread about Scheme, Go, JavaScript, Lua, object identity / the `is` operator, the walrus operator, lambdas, and language popularity are broader thread context about Python ergonomics and language design in general – they should NOT be presented as commentary about `difflib` specifically.

One `SequenceMatcher` anecdote does not prove that `autojunk` is wrong for every diffing workload.

## SequenceMatcher autojunk – what the documentation says

`difflib.SequenceMatcher(isjunk=None, a='', b='', autojunk=True)` – per the [Python 3 standard library documentation](https://docs.python.org/3/library/difflib.html):

- `autojunk` (default `True`): enable automatic junk filtering heuristic
- Automatic junk filtering is applied when `b` has 200 or more elements
- An element is considered "popular" (automatically treated as junk) if it occurs in more than 1% of `b` – strictly greater than. At length 200, that means at least 4 total occurrences (3 duplicates after the first), since 3 occurrences = 2 duplicates = exactly 1.0%, which does NOT satisfy the strict >1% rule
- Popularity / junk state is associated with the second sequence (`b`) specifically – argument order matters
- `ratio()` returns a float in `[0.0, 1.0]` measuring similarity – it is NOT guaranteed to be symmetric
- `quick_ratio()` and `real_quick_ratio()` are upper bounds, NOT replacements for `ratio()`
- `get_matching_blocks()` always ends with a dummy block `(len(a), len(b), 0)`
- `get_opcodes()` describes how to turn `a` into `b` – NOT claimed to be a minimal edit script

See the [CPython source](https://github.com/python/cpython/blob/main/Lib/difflib.py) for the implementation.

## What this lab tests vs. what it does NOT claim

This lab tests **narrow, deterministic string and token matching behavior** of `difflib.SequenceMatcher` in the local CPython interpreter.

It does NOT prove or claim:

- `SequenceMatcher.ratio()` is symmetric
- the ratio is a mathematical metric or distance function
- the ratio is a calibrated probability
- a fixed cutoff is statistically valid
- `autojunk=True` is universally correct
- `autojunk=False` is universally more accurate
- popular elements are equivalent to learned stopwords
- matching blocks produce a minimal edit script
- `quick_ratio()` or `real_quick_ratio()` can replace `ratio()`
- character similarity establishes semantic similarity
- fuzzy string similarity validates entity resolution or deduplication
- the tiny threshold example is a trained classifier
- the ranking-flip example represents production information retrieval
- HN criticism proves the default is a bug for every use case
- HN praise for a Python-traps project proves Python is unsuitable for long-term projects
- type hints alone detect or prevent these runtime behaviors
- this stdlib lab replaces specialist fuzzy matching, information-retrieval, record-linkage, statistical, or machine-learning tools

A human-oriented sequence matcher (Ratcliff/Obershelp "gestalt pattern matching") is fundamentally different from a validated machine-learning similarity model, a retrieval ranker, a deduplication system, or a record-linkage pipeline. Character-level edit similarity does NOT establish semantic similarity, entity identity, or statistical validity.

## Hacker News thread access

The HN thread was read using the bundled real Hacker News CLI, via:

```
python3 ./hackernews get-item --id 37281692
```

(followed by recursive fetching of comment children via the Hacker News Firebase API, tool identifier: `hackernews get-item` / Hacker News API).

Evidence (`hn_comments_sanitized.json`, `hn_thread_evidence.md`) was captured **before** the sentiment summary in this README was prepared.

Sanitized HN evidence retains only relevant public fields (item ID, author, parent ID, timestamp, type, public comment text) for comments about WTFPython as a teaching resource, Python traps in production, typing/testing/tooling, the `SequenceMatcher` autojunk observation, backwards compatibility, quirk frequency, and Python ergonomics. Dead/flagged/deleted comments, profanity-only arguments, and unrelated debates about object identity, walrus syntax, lambdas, Scheme, Lua, JavaScript, and Go are excluded unless needed for carefully attributed broader-context sentences. No direct quotes are included unless their exact text appears in the committed evidence.

## Running

```sh
python3 run_lab.py
python3 -m unittest -v
```

Lab finishes in <1s. Tests finish in <1s.

## Results

See [RESULTS.md](RESULTS.md).

## Verify

See [VERIFY.md](VERIFY.md).
