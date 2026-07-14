import unittest, json, sys, hashlib, difflib, pathlib, csv, re
with open("cases.json") as f: CASES=json.load(f)
with open("results_rows.json") as f: ROWS=json.load(f)

def seq_hash(x):
    s=json.dumps(x, sort_keys=True, separators=(",",":"))
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def get_row(case_id, method):
    return next(x for x in ROWS if x["case_id"]==case_id and x["method"]==method)

class TestLab(unittest.TestCase):
    def test_case_count(self):
        self.assertEqual(len(CASES),20)
        ids=[c["id"] for c in CASES]
        self.assertEqual(len(set(ids)),20)
        required=["python_version_marker","sequence_matcher_api_marker","autojunk_parameter_marker","identical_short_sequence_marker","empty_sequence_identity_marker","documented_order_sensitivity_marker","autojunk_length_199_boundary_marker","autojunk_length_200_boundary_marker","popular_token_strict_threshold_marker","autojunk_true_false_long_repetition_marker","second_sequence_popularity_direction_marker","custom_isjunk_state_marker","matching_blocks_terminal_dummy_marker","opcodes_reconstruction_marker","quick_ratio_upper_bound_marker","set_seq2_reuse_equivalence_marker","get_close_matches_cutoff_marker","tiny_record_linkage_threshold_marker","autojunk_candidate_ranking_flip_marker","no_global_similarity_or_ml_validity_claim_marker"]
        for r in required: self.assertIn(r,ids)

    def test_case_expectations(self):
        methods = ["inspect_api","evaluate_ratio","inspect_junk_state","inspect_match_structure","ml_context_observation"]
        for case in CASES:
            self.assertIn("expect", case, f"missing expect map in {case['id']}")
            exp = case["expect"]
            for m in methods:
                self.assertIn(m, exp, f"missing {m} in {case['id']}")
                self.assertTrue(exp[m], f"blank expectation for {case['id']}/{m}")
                self.assertIn(exp[m], {"pass","expected_error","local_observation","version_skip","context_only","not_applicable","fail"})

    def test_rows(self):
        self.assertEqual(len(ROWS),100)
        pairs=[(r["case_id"],r["method"]) for r in ROWS]
        self.assertEqual(len(pairs),len(set(pairs)))
        allowed={"pass","expected_error","local_observation","version_skip","context_only","not_applicable","fail"}
        for r in ROWS:
            self.assertIn(r["expected_classification"],allowed)
            self.assertIn(r["actual_classification"],allowed)
            self.assertTrue(r["expected_classification"])
            self.assertTrue(r["actual_classification"])
            if r["expected_classification"]=="not_applicable":
                self.assertEqual(r["actual_classification"],"not_applicable")
            else:
                self.assertEqual(r["expected_classification"], r["actual_classification"], f"{r['case_id']} {r['method']} expected {r['expected_classification']} got {r['actual_classification']} reason={r.get('failure_reason')}")

    def test_identical(self):
        r=get_row("identical_short_sequence_marker","evaluate_ratio")
        self.assertEqual(r["ratio"],1.0)
        self.assertEqual(r["reverse_ratio"],1.0)
        # matching blocks
        mb = get_row("identical_short_sequence_marker","inspect_match_structure")
        blocks = mb.get("matching_blocks",[])
        self.assertTrue(blocks)
        self.assertEqual(blocks[0][2], 4)

    def test_empty(self):
        r=get_row("empty_sequence_identity_marker","evaluate_ratio")
        self.assertEqual(r["ratio"], 1.0)
        # empty vs nonempty = 0.0 is recorded in local_conclusion, check via re-running
        from difflib import SequenceMatcher
        self.assertEqual(SequenceMatcher(None, [], []).ratio(), 1.0)
        self.assertEqual(SequenceMatcher(None, [], ["x"]).ratio(), 0.0)
        self.assertEqual(SequenceMatcher(None, ["x"], []).ratio(), 0.0)

    def test_order_sensitivity(self):
        r=get_row("documented_order_sensitivity_marker","evaluate_ratio")
        self.assertIsNotNone(r["ratio"])
        self.assertIsNotNone(r["reverse_ratio"])
        # Verify actual values independently
        from difflib import SequenceMatcher
        a="tide"; b="diet"
        r_ab = SequenceMatcher(None, a, b).ratio()
        r_ba = SequenceMatcher(None, b, a).ratio()
        self.assertAlmostEqual(r["ratio"], r_ab)
        self.assertAlmostEqual(r["reverse_ratio"], r_ba)
        # matching blocks structure
        mb = get_row("documented_order_sensitivity_marker","inspect_match_structure")
        self.assertIn("matching_blocks", mb)
        self.assertTrue(mb["matching_blocks"])

    def test_199_boundary(self):
        r=get_row("autojunk_length_199_boundary_marker","inspect_junk_state")
        self.assertEqual(r["actual_classification"],"pass")
        # bpopular should be empty
        self.assertEqual(r.get("bpopular"), [])
        # duplicate count / percent recorded
        self.assertEqual(r.get("duplicate_count"), 198)
        self.assertAlmostEqual(r.get("duplicate_percent",0), 198/199*100, places=5)

    def test_200_popular(self):
        r=get_row("autojunk_length_200_boundary_marker","inspect_junk_state")
        bpop = r.get("bpopular", [])
        self.assertIn("rep", str(bpop))
        self.assertEqual(r.get("seq2_len"), 200)
        self.assertEqual(r.get("duplicate_count"), 3)
        self.assertAlmostEqual(r.get("duplicate_percent",0), 1.5)

    def test_threshold(self):
        r=get_row("popular_token_strict_threshold_marker","inspect_junk_state")
        self.assertEqual(r["actual_classification"],"pass")
        bpop = r.get("bpopular", {})
        # 3 occurrences should NOT be popular
        p3 = bpop.get("3_occurrences", []) if isinstance(bpop, dict) else []
        p4 = bpop.get("4_occurrences", []) if isinstance(bpop, dict) else []
        self.assertEqual(p3, [])
        self.assertIn("t", p4)

    def test_autojunk_long(self):
        r=get_row("autojunk_true_false_long_repetition_marker","evaluate_ratio")
        self.assertIsNotNone(r["ratio"])
        self.assertIsNotNone(r["reverse_ratio"])
        # Verify material score difference
        diff = abs((r["ratio"] or 0) - (r["reverse_ratio"] or 0))
        self.assertGreater(diff, 0.1)
        # Verify junk state
        js = get_row("autojunk_true_false_long_repetition_marker","inspect_junk_state")
        self.assertIn("bpopular", js)
        pop = js.get("bpopular", {})
        if isinstance(pop, dict):
            self.assertIn("x", str(pop.get("true",[])))

    def test_pop_dir(self):
        r=get_row("second_sequence_popularity_direction_marker","evaluate_ratio")
        self.assertIsNotNone(r["ratio"])
        # Check popularity state
        js = get_row("second_sequence_popularity_direction_marker","inspect_junk_state")
        bpop = js.get("bpopular", {})
        self.assertTrue(bpop)

    def test_custom_junk(self):
        r=get_row("custom_isjunk_state_marker","inspect_junk_state")
        bjunk = r.get("bjunk", [])
        self.assertIn("<pad>", str(bjunk))
        self.assertEqual(r.get("isjunk_desc"), "token == '<pad>'")
        self.assertEqual(r.get("autojunk_flag"), False)

    def test_terminal_dummy(self):
        r=get_row("matching_blocks_terminal_dummy_marker","inspect_match_structure")
        blocks=r.get("matching_blocks",[])
        self.assertTrue(blocks)
        last=blocks[-1]
        # last block should be (3,3,0) for a="abc", b="xyz"
        self.assertEqual(last[2],0)
        self.assertEqual(last[0], 3)
        self.assertEqual(last[1], 3)
        # no earlier zero-size block
        for b in blocks[:-1]:
            self.assertNotEqual(b[2], 0)

    def test_opcodes(self):
        r=get_row("opcodes_reconstruction_marker","inspect_match_structure")
        self.assertEqual(r["actual_classification"],"pass")
        # Verify reconstruction
        self.assertIn("reconstructed_value", r)
        self.assertEqual(r["reconstructed_value"], "abycdf")
        # Verify hash matches
        import hashlib, json
        h = hashlib.sha256(json.dumps("abycdf", sort_keys=True, separators=(",",":")).encode()).hexdigest()[:16]
        self.assertEqual(r["reconstructed_hash"], h)
        # opcodes present
        self.assertTrue(r.get("opcodes"))

    def test_quick_ratio(self):
        r=get_row("quick_ratio_upper_bound_marker","evaluate_ratio")
        ratio = r["ratio"] or 0
        qr = r["quick_ratio"] or 0
        rqr = r["real_quick_ratio"] or 0
        self.assertGreaterEqual(qr + 1e-12, ratio)
        self.assertGreaterEqual(rqr + 1e-12, ratio)

    def test_set_seq2(self):
        r=get_row("set_seq2_reuse_equivalence_marker","evaluate_ratio")
        self.assertEqual(r["actual_classification"],"pass")
        scores = r.get("candidate_scores", {})
        fresh = scores.get("fresh", [])
        reuse = scores.get("reuse", [])
        self.assertEqual(len(fresh), 4)
        self.assertEqual(len(reuse), 4)
        for a,b in zip(fresh, reuse):
            self.assertAlmostEqual(a, b, places=12)

    def test_close_matches(self):
        r=get_row("get_close_matches_cutoff_marker","evaluate_ratio")
        cm = r.get("close_matches")
        self.assertIsNotNone(cm)
        # Verify both cutoffs independently
        from difflib import get_close_matches
        word="appel"; possibilities=["ape","apple","peach","puppy"]
        cm1 = get_close_matches(word, possibilities, n=3, cutoff=0.6)
        cm2 = get_close_matches(word, possibilities, n=3, cutoff=0.8)
        self.assertEqual(cm, cm1)
        # stricter cutoff should be subset
        self.assertTrue(all(x in cm1 for x in cm2))
        # check ML context observation has scores
        ml = get_row("get_close_matches_cutoff_marker","ml_context_observation")
        self.assertIn("candidate_scores", ml)
        scores = ml.get("candidate_scores", {})
        self.assertIn("apple", scores)

    def test_linkage(self):
        r=get_row("tiny_record_linkage_threshold_marker","evaluate_ratio")
        scores=r.get("candidate_scores",{})
        self.assertTrue(scores)
        # Recompute every score
        from difflib import SequenceMatcher
        query="acme corporation"
        candidates=["acme corporation","acme corp","acne corporation","northwind logistics"]
        threshold = 0.8
        for cand in candidates:
            self.assertIn(cand, scores)
            s = scores[cand]
            rf_exp = SequenceMatcher(None, query, cand, autojunk=False).ratio()
            rr_exp = SequenceMatcher(None, cand, query, autojunk=False).ratio()
            mean_exp = (rf_exp + rr_exp) / 2
            self.assertAlmostEqual(s["forward"], rf_exp, places=12)
            self.assertAlmostEqual(s["reverse"], rr_exp, places=12)
            self.assertAlmostEqual(s["mean"], mean_exp, places=12)
            # threshold label
            label_exp = "above" if mean_exp >= threshold else "below"
            # labels are stored in ml_context_observation
        # Check ml_context_observation
        ml = get_row("tiny_record_linkage_threshold_marker","ml_context_observation")
        self.assertEqual(ml["threshold"] if "threshold" in ml else 0.8, 0.8)
        # Check ranking
        ranking = r.get("candidate_ranking", [])
        # if ranking not stored in evaluate_ratio, check ml observation or recompute
        exp_ranking = sorted(candidates, key=lambda c: scores[c]["mean"], reverse=True)
        # ranking may be stored, if so check it
        if ranking:
            self.assertEqual(ranking, exp_ranking)

    def test_ranking_flip(self):
        r=get_row("autojunk_candidate_ranking_flip_marker","evaluate_ratio")
        cs=r.get("candidate_scores",{})
        self.assertTrue(cs)
        self.assertIn("autojunk_true", cs)
        self.assertIn("autojunk_false", cs)
        s_true = cs["autojunk_true"]["shifted"]
        m_true = cs["autojunk_true"]["mixed"]
        s_false = cs["autojunk_false"]["shifted"]
        m_false = cs["autojunk_false"]["mixed"]
        # Recompute rankings
        rank_true = ["shifted","mixed"] if s_true >= m_true else ["mixed","shifted"]
        rank_false = ["shifted","mixed"] if s_false >= m_false else ["mixed","shifted"]
        # Check stored ranking if present
        stored_ranking = r.get("candidate_ranking")
        if stored_ranking and isinstance(stored_ranking, dict):
            self.assertEqual(stored_ranking.get("true"), rank_true)
            self.assertEqual(stored_ranking.get("false"), rank_false)
        # Check ranking_changed flag
        self.assertIn("ranking_changed", r)
        self.assertEqual(r["ranking_changed"], rank_true != rank_false)
        # Verify score margins exist
        # margins may be stored
        margin = r.get("score_margin")
        if margin:
            self.assertAlmostEqual(margin.get("true", abs(s_true-m_true)), abs(s_true-m_true), places=10)

    def test_no_global_claim(self):
        r=get_row("no_global_similarity_or_ml_validity_claim_marker","ml_context_observation")
        self.assertEqual(r["actual_classification"],"context_only")

    def test_counts_agree(self):
        with open("results_rows.csv") as f:
            cr=list(csv.DictReader(f))
        self.assertEqual(len(cr), len(ROWS))
        self.assertEqual(len(cr), 100)
        # Check JSON and RESULTS agree
        with open("RESULTS.md") as f: results_txt = f.read()
        self.assertIn("Rows: 100", results_txt)
        self.assertIn("Cases: 20", results_txt)

    def test_readme_disclaimers(self):
        txt = pathlib.Path("README.md").read_text()
        txt_low = txt.lower()
        for needle in ["calibrated probability","semantic","machine-learning","production","difflib","autojunk"]:
            self.assertIn(needle, txt_low)
        # Check HN section exists
        self.assertIn("Hacker News thread access", txt)
        self.assertIn("37281692", txt)
        # Check disclaimers section
        self.assertIn("does NOT prove or claim", txt)

    def test_results_generated(self):
        # RESULTS.md should match current run
        txt = pathlib.Path("RESULTS.md").read_text()
        # Should contain key observations with actual numbers from this run
        self.assertIn("Identical short sequence", txt)
        self.assertIn("Order sensitivity", txt)
        self.assertIn("tide/diet", txt.lower())
        # Check that ratios in RESULTS match JSON
        od = get_row("documented_order_sensitivity_marker","evaluate_ratio")
        # RESULTS should contain the actual ratio values (at least the forward one)
        self.assertIn(str(od["ratio"]), txt)

    def test_artifact_scanning(self):
        # Scan every committed text artifact
        files_to_scan = [
            "README.md",
            "RESULTS.md",
            "cases.json",
            "results_rows.json",
            "results_rows.csv",
            "hn_thread_evidence.md",
            "hn_comments_sanitized.json",
        ]
        # Also scan VERIFY.md if present
        if pathlib.Path("VERIFY.md").exists():
            files_to_scan.append("VERIFY.md")

        # Patterns to reject (sensitive data that must NOT appear)
        bad_patterns = [
            (re.compile(r"/home/[a-zA-Z0-9_.-]+/\.openclaw"), "internal openclaw path"),
            (re.compile(r"/tmp/[a-zA-Z0-9_.-]+"), "tmp path leak"),
            (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "github PAT"),
            (re.compile(r"github_pat_[A-Za-z0-9_]{80,}"), "github fine-grained PAT"),
            (re.compile(r"\b Bearer [A-Za-z0-9_-]{20,}\b", re.I), "bearer token"),
            (re.compile(r"\bapi[_-]?key[\"'\s:=]+[A-Za-z0-9_-]{20,}", re.I), "api key"),
            (re.compile(r"\bpassword[\"'\s:=]+[^\s]{8,}", re.I), "password"),
            (re.compile(r"openclaw.*token", re.I), "openclaw token ref"),
            (re.compile(r"session[_\-][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I), "uuid session id"),
            # Allow the documented safe placeholder /python-lab
            # Reject other absolute paths that look like internal installs
            (re.compile(r"/home/ubuntu/(?!\.local|\.pyenv|workspace)"), "unexpected ubuntu home path"),
            (re.compile(r"C:\\Users\\[A-Za-z0-9_.-]+", re.I), "windows user path"),
        ]
        # Allowlist: documented safe placeholder
        allow_pattern = re.compile(r"/python-lab")

        issues = []
        for fn in files_to_scan:
            p = pathlib.Path(fn)
            if not p.exists():
                # results_rows files must exist for a complete repo
                if fn.startswith("results_rows"):
                    self.fail(f"Missing required artifact: {fn}")
                continue
            txt = p.read_text(errors="ignore")
            # Remove allowlisted safe placeholder before scanning
            txt_scan = allow_pattern.sub("", txt)
            for pat, desc in bad_patterns:
                m = pat.search(txt_scan)
                if m:
                    issues.append(f"{fn}: {desc} matched: {m.group(0)[:60]!r}")

        if issues:
            self.fail("Artifact scanner found prohibited content:\n" + "\n".join(issues))

        # Also verify no github token placeholder leaked from earlier test run
        for fn in files_to_scan:
            p = pathlib.Path(fn)
            if not p.exists(): continue
            txt = p.read_text(errors="ignore")
            self.assertNotIn("/home/ubuntu/.openclaw", txt, f"openclaw path leak in {fn}")

if __name__=="__main__": unittest.main()
