#!/usr/bin/env python3
"""nk_curator.py — Negative Knowledge production module for §4.

Canonical, reusable interface for producing structured NK records from
3-round BKdV-S program traces. The dual-pass model:

  - ``produce_per_round(program_id, round_num, program_dir)``  — depth-1
    record from ONE round's artifacts.
  - ``produce_deep(program_id, program_dir)``                  — depth-3
    synthesis from all three rounds plus hypothesis.md.

The schemas mirror section 3's (with a small section-4 extension for
``is_trivial`` / ``trivial_degree``); see paper §4 and appendix
``appendix:bkdv-bank`` for the rationale.

================================================================
Programmatic use
================================================================

    >>> from nk_curator import NKCurator
    >>>
    >>> curator = NKCurator(model="default")
    >>>
    >>> # depth-1 (one round)
    >>> rec = curator.produce_per_round(
    ...     program_id="BKdV-S6",
    ...     round_num=1,
    ...     program_dir="logs/stage1/BKdV-S6",
    ...     output_path="nk_records/BKdV-S6_r1.json",
    ... )
    >>>
    >>> # depth-3 synthesis across all 3 rounds
    >>> rec = curator.produce_deep(
    ...     program_id="BKdV-S6",
    ...     program_dir="logs/stage1/BKdV-S6",
    ...     output_path="nk_records/BKdV-S6_deep.json",
    ... )

================================================================
Schemas (compatible with section 3 schema; small §4 extension)
================================================================

Single-round (depth-1):
    {task_id, round, attempted_route, observation, failure{...},
     rationale, recommended_alternative,
     is_trivial, trivial_degree}                     -- §4 extension

Deep synthesis (depth ≥ 2):
    {task_id, depth, rounds_summary[], ruled_out_routes[],
     synthesised_diagnosis, failure{...}, rationale,
     recommended_alternative,
     is_trivial, trivial_degree}                     -- §4 extension

"failure" subfields: layer, scope, degree, recommended_action, risk
  (controlled vocabulary; see SCHEMA_* constants below).
"""
from __future__ import annotations
import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Optional, List

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from _paths import CURATOR_PROMPTS

from dispatch_subagent import resolve_model, run_subagent


# ============================================================
# Schema constants (controlled vocabulary)
# ============================================================

LAYERS = ("implementation_failure", "communication_failure",
          "method_failure", "hypothesis_failure", "measurement_failure")
SCOPES = ("local_failure", "regime_bound_failure", "general_failure")
DEGREES = ("contradicted", "partial", "inconclusive", "unstable",
           "artifact_driven", "overclaimed")
RECOMMENDED_ACTIONS = ("retry", "change_method", "narrow_claim",
                       "abandon_route")
RISKS = ("low_risk_omission", "medium_risk_drift",
         "high_risk_false_progress")

SCHEMA_BASE_FIELDS = ("task_id", "attempted_route", "observation",
                      "failure", "rationale", "recommended_alternative")
SCHEMA_DEEP_EXTRA = ("depth", "rounds_summary", "ruled_out_routes",
                     "synthesised_diagnosis")


def validate_nk(nk: dict, depth: int = 1) -> List[str]:
    """Return a list of schema violations (empty list = valid)."""
    issues: List[str] = []
    if depth == 1:
        required = SCHEMA_BASE_FIELDS
    else:
        # depth >= 2: drop attempted_route + observation at top level
        # (they live per-round inside rounds_summary)
        required = tuple(f for f in SCHEMA_BASE_FIELDS
                         if f not in ("attempted_route", "observation"))
    for fld in required:
        if fld not in nk:
            issues.append(f"missing base field: {fld}")

    f = nk.get("failure", {})
    if isinstance(f, dict):
        for sub in ("layer", "scope", "degree", "recommended_action", "risk"):
            if sub not in f:
                issues.append(f"failure.{sub} missing")
        if f.get("layer") not in LAYERS:
            issues.append(f"failure.layer not in {LAYERS}")
        if f.get("scope") not in SCOPES:
            issues.append(f"failure.scope not in {SCOPES}")
        if f.get("degree") not in DEGREES:
            issues.append(f"failure.degree not in {DEGREES}")
        if f.get("recommended_action") not in RECOMMENDED_ACTIONS:
            issues.append(f"failure.recommended_action not in {RECOMMENDED_ACTIONS}")
        if f.get("risk") not in RISKS:
            issues.append(f"failure.risk not in {RISKS}")
    else:
        issues.append("failure block is not a dict")

    if depth >= 2:
        for fld in SCHEMA_DEEP_EXTRA:
            if fld not in nk:
                issues.append(f"missing deep field: {fld}")
        rs = nk.get("rounds_summary")
        if not isinstance(rs, list) or len(rs) < 2:
            issues.append("rounds_summary should be a list of ≥ 2 entries")
        rr = nk.get("ruled_out_routes")
        if not isinstance(rr, list) or len(rr) < 2:
            issues.append("ruled_out_routes should be a list of ≥ 2 entries")
    return issues


# ============================================================
# Prompt materialisation
# ============================================================

class CuratorPrompt:
    """Wraps a curator prompt template with substitution + I/O hooks.

    The two canonical templates live in section4_reproduce/curator_prompts/:
      - per_round_template.md   for depth-1 records
      - deep_template.md         for depth-≥2 synthesis

    Each contains placeholders like ``{program_id}``, ``{round_num}``,
    ``{round_dir}``, ``{program_dir}``, ``{nk_records_dir}``.
    """

    def __init__(self, template_path: pathlib.Path):
        self.template_path = pathlib.Path(template_path)
        self.body = self.template_path.read_text()

    def materialize(self, **subs: str) -> str:
        out = self.body
        for k, v in subs.items():
            out = out.replace("{" + k + "}", str(v))
        return out


# ============================================================
# Curator dispatch
# ============================================================

@dataclass
class CurationResult:
    program_id: str
    depth: int
    output_path: str
    nk: dict
    schema_issues: List[str]
    dispatch: dict  # tokens, tool_uses, duration, etc.


class NKCurator:
    """Produce structured NK records from BKdV-S program traces.

    Parameters
    ----------
    model : str
        Model name understood by the configured agent command.
    curator_prompts_dir : pathlib.Path, optional
        Directory containing per_round_template.md and deep_template.md.
        Defaults to section4_reproduce/curator_prompts/.
    """

    def __init__(self, model: str = "default",
                 curator_prompts_dir: Optional[pathlib.Path] = None):
        self.model = resolve_model(model)
        self.curator_prompts_dir = curator_prompts_dir or CURATOR_PROMPTS
        for fname in ("per_round_template.md", "deep_template.md"):
            if not (self.curator_prompts_dir / fname).exists():
                raise FileNotFoundError(
                    f"missing curator template: "
                    f"{self.curator_prompts_dir / fname}"
                )

    # -------- prompt building --------

    def materialize_per_round(
        self, program_id: str, round_num: int, program_dir: pathlib.Path,
        nk_records_dir: pathlib.Path, research_question: str,
    ) -> str:
        tpl = CuratorPrompt(self.curator_prompts_dir / "per_round_template.md")
        return tpl.materialize(
            program_id=program_id,
            round_num=round_num,
            round_dir=str(pathlib.Path(program_dir) / f"round{round_num}"),
            program_dir=str(program_dir),
            nk_records_dir=str(nk_records_dir),
            research_question=research_question,
        )

    def materialize_deep(
        self, program_id: str, program_dir: pathlib.Path,
        nk_records_dir: pathlib.Path, research_question: str,
    ) -> str:
        tpl = CuratorPrompt(self.curator_prompts_dir / "deep_template.md")
        return tpl.materialize(
            program_id=program_id,
            program_dir=str(program_dir),
            nk_records_dir=str(nk_records_dir),
            research_question=research_question,
        )

    # -------- dispatch + write --------

    def produce_per_round(
        self, program_id: str, round_num: int,
        program_dir: pathlib.Path,
        output_path: pathlib.Path,
        research_question: str = "(see program prompt)",
    ) -> CurationResult:
        """Dispatch the per-round curator and write a depth-1 NK JSON."""
        prompt = self.materialize_per_round(
            program_id, round_num, program_dir,
            nk_records_dir=pathlib.Path(output_path).parent,
            research_question=research_question,
        )
        round_dir = pathlib.Path(program_dir) / f"round{round_num}"
        read_allow = {str(round_dir / f) for f in
                      ("candidate.py", "exec.log", "reasoning.md")}
        read_allow.add(str(pathlib.Path(program_dir) / "research_state.jsonl"))
        write_allow = {str(output_path)}
        dispatch = run_subagent(
            prompt=prompt, model=self.model,
            read_allowlist=read_allow, write_allowlist=write_allow,
        )
        nk = json.loads(pathlib.Path(output_path).read_text())
        issues = validate_nk(nk, depth=1)
        return CurationResult(program_id, 1, str(output_path), nk, issues, dispatch)

    def produce_deep(
        self, program_id: str, program_dir: pathlib.Path,
        output_path: pathlib.Path,
        research_question: str = "(see program prompt)",
    ) -> CurationResult:
        """Dispatch the deep curator and write a depth-3 NK JSON."""
        prompt = self.materialize_deep(
            program_id, program_dir,
            nk_records_dir=pathlib.Path(output_path).parent,
            research_question=research_question,
        )
        read_allow: set = set()
        for r in (1, 2, 3):
            rd = pathlib.Path(program_dir) / f"round{r}"
            for fname in ("candidate.py", "exec.log", "reasoning.md"):
                read_allow.add(str(rd / fname))
        read_allow.add(str(pathlib.Path(program_dir) / "research_state.jsonl"))
        read_allow.add(str(pathlib.Path(program_dir) / "hypothesis.md"))
        write_allow = {str(output_path)}
        dispatch = run_subagent(
            prompt=prompt, model=self.model,
            read_allowlist=read_allow, write_allowlist=write_allow,
        )
        nk = json.loads(pathlib.Path(output_path).read_text())
        depth = nk.get("depth", 3)
        issues = validate_nk(nk, depth=depth)
        return CurationResult(program_id, depth, str(output_path), nk, issues, dispatch)


# ============================================================
# CLI
# ============================================================

def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Dispatch one curator sub-agent.")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p1 = sp.add_parser("per_round", help="Produce a depth-1 NK from one round.")
    p1.add_argument("--program-id", required=True)
    p1.add_argument("--round", type=int, required=True, choices=[1, 2, 3])
    p1.add_argument("--program-dir", required=True, type=pathlib.Path)
    p1.add_argument("--output", required=True, type=pathlib.Path)
    p1.add_argument("--model", default="default")

    p2 = sp.add_parser("deep", help="Produce a depth-3 deep NK synthesis.")
    p2.add_argument("--program-id", required=True)
    p2.add_argument("--program-dir", required=True, type=pathlib.Path)
    p2.add_argument("--output", required=True, type=pathlib.Path)
    p2.add_argument("--model", default="default")

    args = ap.parse_args()
    curator = NKCurator(model=args.model)
    if args.cmd == "per_round":
        res = curator.produce_per_round(
            args.program_id, args.round, args.program_dir, args.output)
    else:
        res = curator.produce_deep(
            args.program_id, args.program_dir, args.output)
    print(f"wrote {res.output_path}")
    print(f"  depth: {res.depth}")
    print(f"  schema issues: {len(res.schema_issues)}")
    for s in res.schema_issues:
        print(f"    - {s}")
    print(f"  tokens: {res.dispatch.get('total_tokens')}, "
          f"tool_uses: {res.dispatch.get('tool_uses')}")


if __name__ == "__main__":
    _cli()
