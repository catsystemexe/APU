import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

API_URL = "http://0.0.0.0:8000/api/chat"
TEST_DIR = Path("kb/tests")
REPORT_DIR = Path("reports")


def post_chat(message: str) -> dict:
    payload = json.dumps({"message": message}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def codes(items):
    return [x.get("code") for x in (items or []) if x.get("code")]


def primary_zone(zones):
    if not zones:
        return None
    for z in zones:
        if z.get("role") == "dominant":
            return z.get("code")
    return zones[0].get("code")


def check_contains(actual, expected, label, fails):
    for x in expected or []:
        if x not in actual:
            fails.append(f"{label}: missing {x}; actual={actual}")


def check_not_contains(actual, forbidden, label, fails):
    for x in forbidden or []:
        if x in actual:
            fails.append(f"{label}: forbidden {x}; actual={actual}")


def evaluate(case, data):
    exp = case.get("expected", {})
    pipe = data["meta"]["pipeline"]

    actual_mode = pipe.get("output_mode")
    actual_flags = pipe.get("validation", {}).get("flags", [])
    actual_blocks = codes(pipe.get("blocks", []))
    actual_profiles = codes(pipe.get("profiles", []))
    actual_zones = codes(pipe.get("zones", []))
    actual_primary_zone = primary_zone(pipe.get("zones", []))
    iq = pipe.get("input_quality", {}) or {}
    actual_overall_confidence = (iq.get("overall_confidence") or {}).get("level") or iq.get("confidence")
    evidence_summary = ((iq.get("evidence") or {}).get("summary") or {})
    notepad_state = ((iq.get("notepad") or {}).get("case_state") or {})
    notepad_state = ((iq.get("notepad") or {}).get("case_state") or {})

    fails = []

    if "output_mode" in exp and actual_mode != exp["output_mode"]:
        fails.append(f"output_mode: expected {exp['output_mode']}, got {actual_mode}")

    if "primary_zone" in exp and actual_primary_zone != exp["primary_zone"]:
        fails.append(f"primary_zone: expected {exp['primary_zone']}, got {actual_primary_zone}")

    if "overall_confidence" in exp and actual_overall_confidence != exp["overall_confidence"]:
        fails.append(f"overall_confidence: expected {exp['overall_confidence']}, got {actual_overall_confidence}")

    check_contains(actual_flags, exp.get("must_have_flags"), "flags", fails)
    check_not_contains(actual_flags, exp.get("must_not_have_flags"), "flags", fails)

    check_contains(actual_blocks, exp.get("must_include_blocks"), "blocks", fails)
    check_not_contains(actual_blocks, exp.get("must_not_include_blocks"), "blocks", fails)

    check_contains(actual_profiles, exp.get("must_include_profiles"), "profiles", fails)
    check_not_contains(actual_profiles, exp.get("must_not_include_profiles"), "profiles", fails)

    check_contains(actual_zones, exp.get("must_include_zones"), "zones", fails)
    check_not_contains(actual_zones, exp.get("must_not_include_zones"), "zones", fails)

    evidence_checks = {
        "evidence_min_observables": "observable_count",
        "evidence_min_labels": "label_count",
        "evidence_min_trends": "trend_intensity_count",
        "evidence_min_contexts": "context_candidate_count",
        "evidence_min_zones": "zone_count",
    }
    for exp_key, actual_key in evidence_checks.items():
        if exp_key in exp:
            actual_n = int(evidence_summary.get(actual_key) or 0)
            expected_n = int(exp.get(exp_key) or 0)
            if actual_n < expected_n:
                fails.append(f"{exp_key}: expected >= {expected_n}, got {actual_n}")

    notepad_checks = {
        "notepad_min_confirmed_observations": "case_info_observable_anchor",
        "notepad_min_uncertain_observations": "uncertain_observations",
        "notepad_min_environmental_triggers": "environmental_triggers",
        "notepad_min_uncertain_hypotheses": "uncertain_hypotheses",
        "notepad_min_contradictions": "contradictions",
        "notepad_min_open_questions": "open_questions",
        "notepad_min_safety_notes": "safety_notes",
        "notepad_min_next_steps": "next_steps",
    }
    for exp_key, section in notepad_checks.items():
        if exp_key in exp:
            if section == "case_info_observable_anchor":
                actual_n = len(((notepad_state.get("case_info") or {}).get("observable_anchor")) or [])
            else:
                actual_n = len(notepad_state.get(section) or [])

            expected_n = int(exp.get(exp_key) or 0)
            if actual_n < expected_n:
                fails.append(f"{exp_key}: expected >= {expected_n}, got {actual_n}")

    notepad_checks = {
        "notepad_min_confirmed_observations": "case_info_observable_anchor",
        "notepad_min_uncertain_observations": "uncertain_observations",
        "notepad_min_environmental_triggers": "environmental_triggers",
        "notepad_min_uncertain_hypotheses": "uncertain_hypotheses",
        "notepad_min_contradictions": "contradictions",
        "notepad_min_open_questions": "open_questions",
        "notepad_min_safety_notes": "safety_notes",
        "notepad_min_next_steps": "next_steps",
    }
    for exp_key, section in notepad_checks.items():
        if exp_key in exp:
            if section == "case_info_observable_anchor":
                actual_n = len(((notepad_state.get("case_info") or {}).get("observable_anchor")) or [])
            else:
                actual_n = len(notepad_state.get(section) or [])

            expected_n = int(exp.get(exp_key) or 0)
            if actual_n < expected_n:
                fails.append(f"{exp_key}: expected >= {expected_n}, got {actual_n}")

    return {
        "id": case["id"],
        "input": case["input"],
        "pass": not fails,
        "fails": fails,
        "actual": {
            "output_mode": actual_mode,
            "primary_zone": actual_primary_zone,
            "flags": actual_flags,
            "blocks": actual_blocks,
            "profiles": actual_profiles,
            "zones": actual_zones,
            "specificity": pipe.get("input_quality", {}).get("specificity"),
            "overall_confidence": pipe.get("input_quality", {}).get("overall_confidence"),
            "evidence_summary": ((pipe.get("input_quality", {}) or {}).get("evidence") or {}).get("summary"),
            "case_id": pipe.get("case_id"),
            "notepad_summary": {
                "case_info_observable_anchor": len(((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("case_info") or {}).get("observable_anchor") or []),
                "uncertain_observations": len((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("uncertain_observations") or []),
                "open_questions": len((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("open_questions") or []),
                "safety_notes": len((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("safety_notes") or []),
            },
            "case_id": pipe.get("case_id"),
            "notepad_summary": {
                "case_info_observable_anchor": len(((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("case_info") or {}).get("observable_anchor") or []),
                "uncertain_observations": len((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("uncertain_observations") or []),
                "open_questions": len((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("open_questions") or []),
                "safety_notes": len((((pipe.get("input_quality", {}) or {}).get("notepad") or {}).get("case_state") or {}).get("safety_notes") or []),
            },
        },
    }


def load_cases():
    cases = []
    for path in sorted(TEST_DIR.glob("T*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a list")
        for case in data:
            case["_file"] = str(path)
            cases.append(case)
    return cases


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    cases = load_cases()
    results = []

    for case in cases:
        try:
            data = post_chat(case["input"])
            result = evaluate(case, data)
        except Exception as e:
            result = {
                "id": case.get("id"),
                "input": case.get("input"),
                "pass": False,
                "fails": [f"runner_error: {type(e).__name__}: {e}"],
                "actual": {},
            }

        results.append(result)

        status = "PASS" if result["pass"] else "FAIL"
        print(f"{status} {result['id']}")
        for f in result["fails"]:
            print(f"  - {f}")

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"test_run_{ts}.json"
    report_path.write_text(json.dumps({
        "summary": {
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total else 0,
        },
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"SUMMARY: {passed}/{total} PASS")
    print(f"REPORT: {report_path}")

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
