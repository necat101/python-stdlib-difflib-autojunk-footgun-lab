# Results

Python executable: /usr/bin/python3
Python version: 3.12.3
Implementation: CPython
Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39

SequenceMatcher available: True
autojunk parameter available: True
get_close_matches available: True

Cases: 20
Methods: 5
Rows: 100

Classifications:
- pass: 22
- local_observation: 8
- context_only: 1
- not_applicable: 69

## Observations

Identical short sequence: ratio 1.0 (autojunk true=1.0, false=1.0), matching blocks cover full input.

Empty sequence: empty-empty=1.0, empty-nonempty=0.0, nonempty-empty=0.0

Order sensitivity (tide/diet): forward 0.25, reverse 0.5, diff 0.25

199-element boundary: bpopular=[] – heuristic not activated by length alone below 200. duplicates=198 (99.49748743718592%)

200-element boundary: bpopular=['rep'] – repeated token marked popular.

Strict >1% threshold: {'3_occurrences': [], '4_occurrences': ['t']} – 3 occurrences (2 dup, 1.0%) NOT popular; 4 occurrences (3 dup, 1.5%) popular.

Autojunk true vs false long repetition: true=0.005, false=0.995, diff=0.99

Second-sequence popularity direction: forward=0.006666666666666667, reverse=0.66 – popularity is second-sequence specific.

Custom isjunk: bjunk=['<pad>'] – explicit junk token present.

Matching blocks terminal dummy: [(3, 3, 0)] – final block is zero-size at (len(a),len(b)).

Opcodes reconstruction: reconstructed='abycdf' – opcodes reconstruct target exactly.

Quick ratio upper bound: ratio=0.75, quick=0.75, real_quick=1.0 – both upper bounds ≥ exact ratio.

set_seq2() reuse: {'fresh': [0.8235294117647058, 0.5882352941176471, 0.8888888888888888, 0.5555555555555556], 'reuse': [0.8235294117647058, 0.5882352941176471, 0.8888888888888888, 0.5555555555555556]} – fresh and reuse scores identical.

get_close_matches cutoff: close_matches=['apple', 'ape'], cutoff=0.6

Tiny record-linkage: scores={'acme corporation': {'forward': 1.0, 'reverse': 1.0, 'mean': 1.0}, 'acme corp': {'forward': 0.72, 'reverse': 0.72, 'mean': 0.72}, 'acne corporation': {'forward': 0.9375, 'reverse': 0.9375, 'mean': 0.9375}, 'northwind logistics': {'forward': 0.2857142857142857, 'reverse': 0.2857142857142857, 'mean': 0.2857142857142857}}, threshold=0.8 (arbitrary, NOT ML)

Ranking flip: {'autojunk_true': {'shifted': 0.005, 'mixed': 0.505}, 'autojunk_false': {'shifted': 0.995, 'mixed': 0.505}}, ranking_changed=True – local observation only, NOT a retrieval benchmark.

Version skips: 0
Failures: 0

Total runtime: 0.039s

## Disclaimers

This lab does NOT prove that SequenceMatcher.ratio() is symmetric, a mathematical metric, a calibrated probability, that a fixed cutoff is statistically valid, that autojunk=True/False is universally correct, that popular elements equal learned stopwords, that matching blocks are a minimal edit script, that quick_ratio() can replace ratio(), that character similarity establishes semantic similarity, that fuzzy string similarity validates entity resolution, that the tiny threshold example is a trained classifier, that the ranking-flip is production IR, that HN criticism proves the default is a bug for every use case, that HN praise proves Python is unsuitable for long-term projects, that type hints prevent these runtime behaviors, or that this stdlib lab replaces specialist fuzzy matching / IR / record-linkage / ML tools.
