# scripts/test_notepad_caseinfo_regression.py

from backend.pipeline.orchestrator import run_pipeline
from backend.pipeline.schemas import APURequest
import json
import sys


TESTS = [
    # --------------------------------------------------
    # 1. NO OBSERVABLE
    # --------------------------------------------------
    {
        "id": "NP_NO_OBS_NEED_ONLY",
        "msg": "Potřebuji rychle zklidnit situaci.",
        "expect": {
            "mode": "LOW_DATA",
            "observable_count": 0,
            "warning_min": 0,
            "need_min": 1,
            "question_min": 1,
        }
    },
    {
        "id": "NP_NO_OBS_CONTEXT_ONLY",
        "msg": "Děje se to hlavně u jedné učitelky.",
        "expect": {
            "mode": "LOW_DATA",
            "observable_count": 0,
            "warning_min": 0,
            "context_min": 1,
            "question_min": 1,
        }
    },

    # --------------------------------------------------
    # 2. LABEL ONLY
    # --------------------------------------------------
    {
        "id": "NP_LABEL_ZLOBI",
        "msg": "Dítě zlobí.",
        "expect": {
            "mode": "LOW_DATA",
            "observable_count": 0,
            "warning_min": 1,
            "question_min": 1,
        }
    },
    {
        "id": "NP_LABEL_MANIPULUJE",
        "msg": "Dítě manipuluje s učitelkou.",
        "expect": {
            "mode": "LOW_DATA",
            "observable_count": 0,
            "warning_min": 1,
            "need_min": 1,
            "question_min": 1,
        }
    },

    # --------------------------------------------------
    # 3. INCOMPLETE OBSERVABLE FRAGMENT
    # --------------------------------------------------
    {
        "id": "NP_FRAGMENT_PLACE",
        "msg": "Pláče.",
        "expect": {
            "mode": "LOW_DATA",
            "observable_count": 0,
            "warning_min": 1,
            "question_min": 1,
        }
    },
    {
        "id": "NP_FRAGMENT_BEHA",
        "msg": "Běhá.",
        "expect": {
            "mode": "LOW_DATA",
            "observable_count": 0,
            "warning_min": 1,
            "question_min": 1,
        }
    },

    # --------------------------------------------------
    # 4. VALID OBSERVABLE
    # --------------------------------------------------
    {
        "id": "NP_VALID_TOYS",
        "msg": "Bere dětem hračky a odmítá je vrátit.",
        "expect": {
            "mode": "PARTIAL",
            "observable_count": 1,
            "warning_max": 0,
            "question_min": 1,
        }
    },
    {
        "id": "NP_VALID_OBS_PLUS_NEED",
        "msg": "Bere dětem hračky, potřebuji rychle zklidnit situaci.",
        "expect": {
            "mode": "PARTIAL",
            "observable_count": 1,
            "warning_max": 0,
            "need_min": 1,
            "question_max": 0,
        }
    },

    # --------------------------------------------------
    # 5. REGRESSION — odmítá cleanup
    # --------------------------------------------------
    {
        "id": "NP_REGRESSION_ODMITA_RETURN",
        "msg": "Bere dětem hračky a odmítá je vrátit.",
        "expect": {
            "mode": "PARTIAL",
            "observable_count": 1,   # nesmí být 2
            "warning_max": 0,
        }
    },
    {
        "id": "NP_REGRESSION_ODMITA_WORK",
        "msg": "Dítě odmítá pracovat.",
        "expect": {
            "mode": "PARTIAL",
            "observable_count": 1,
            "warning_max": 0,
        }
    },
]


def texts(items):
    return [
        (x.get("text") or x.get("question") or "").strip()
        for x in (items or [])
    ]


def run_case(test):
    msg = test["msg"]
    exp = test["expect"]

    r = run_pipeline(
        APURequest(message=msg, state={}),
        kb_context=""
    )

    cs = (
        ((r.meta.input_quality or {}).get("notepad") or {})
        .get("case_state")
    ) or {}

    ci = cs.get("case_info") or {}

    obs = ci.get("observable_anchor") or []
    warn = ci.get("teacher_interpretation_labels") or []
    need = ci.get("pedagogical_need") or []
    ctx = ci.get("context") or []
    q = cs.get("open_questions") or []

    print("\n" + "=" * 80)
    print(test["id"])
    print("INPUT:", msg)
    print("mode:", r.meta.output_mode)
    print("flags:", r.meta.validation.get("flags"))
    print("OBS:", json.dumps(texts(obs), ensure_ascii=False))
    print("LABEL/WARN:", json.dumps(texts(warn), ensure_ascii=False))
    print("NEED:", json.dumps(texts(need), ensure_ascii=False))
    print("CTX:", json.dumps(texts(ctx), ensure_ascii=False))
    print("QUESTIONS:", json.dumps(texts(q), ensure_ascii=False))

    errors = []

    if r.meta.output_mode != exp["mode"]:
        errors.append(
            f"mode expected {exp['mode']}, got {r.meta.output_mode}"
        )

    if len(obs) != exp["observable_count"]:
        errors.append(
            f"observable_count expected {exp['observable_count']}, got {len(obs)}"
        )

    if "warning_min" in exp and len(warn) < exp["warning_min"]:
        errors.append(
            f"warnings expected >= {exp['warning_min']}, got {len(warn)}"
        )

    if "warning_max" in exp and len(warn) > exp["warning_max"]:
        errors.append(
            f"warnings expected <= {exp['warning_max']}, got {len(warn)}"
        )

    if "need_min" in exp and len(need) < exp["need_min"]:
        errors.append(
            f"need expected >= {exp['need_min']}, got {len(need)}"
        )

    if "context_min" in exp and len(ctx) < exp["context_min"]:
        errors.append(
            f"context expected >= {exp['context_min']}, got {len(ctx)}"
        )

    if "question_min" in exp and len(q) < exp["question_min"]:
        errors.append(
            f"questions expected >= {exp['question_min']}, got {len(q)}"
        )

    if "question_max" in exp and len(q) > exp["question_max"]:
        errors.append(
            f"questions expected <= {exp['question_max']}, got {len(q)}"
        )

    return errors


def main():
    all_errors = []

    for test in TESTS:
        errs = run_case(test)
        if errs:
            for e in errs:
                all_errors.append(f"{test['id']}: {e}")

    print("\n" + "=" * 80)

    if all_errors:
        print("FAIL")
        for e in all_errors:
            print("-", e)
        sys.exit(1)

    print("PASS all notepad case_info regression tests")


if __name__ == "__main__":
    main()
    