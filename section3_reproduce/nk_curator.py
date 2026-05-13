#!/usr/bin/env python3
"""nk_curator.py — Negative Knowledge production module.

This is the canonical, reusable interface for producing structured
negative-knowledge (NK) records from failed attempts. It encapsulates:

  1. **The 6-field bounded failure schema** (see ``SCHEMA_BASE``)
     plus the depth-N extension fields (see ``SCHEMA_DEEP``).
  2. **The curator prompt templates** under ``prompts/``. Prompts are
     first-class: the same module can be re-pointed at any template
     directory, and templates can be overridden per call.
  3. **Sub-agent dispatch** via the Anthropic API, with a constrained
     Read/Write tool-use loop, audit-record capture, and schema
     validation of the resulting NK JSON.

Two operations are supported, distinguished by *depth*:

  - ``curator.produce_depth1(...)`` — read **one round** of failure
    artifacts and write a depth-1 NK record. Used when distilling a
    single failed attempt into one summary.

  - ``curator.produce_deep(...)`` — read **N rounds** of failure
    artifacts (typically a Self-Debug trajectory) and write a deep
    NK record with cross-round synthesis fields
    (``rounds_summary``, ``ruled_out_routes``,
    ``synthesised_diagnosis``).

================================================================
Programmatic use
================================================================

    >>> from nk_curator import NKCurator, FailureArtifacts
    >>>
    >>> curator = NKCurator(model="claude-sonnet-4-5")
    >>>
    >>> # depth-1: one failed round
    >>> nk = curator.produce_depth1(
    ...     task_id="072",
    ...     task_inst="Map Sub01 EEG signals to Sub03 ...",
    ...     round_artifacts=FailureArtifacts(
    ...         candidate="path/to/round1/candidate.py",
    ...         exec_log="path/to/round1/exec.log",
    ...         eval_log="path/to/round1/eval.log",
    ...         reasoning="path/to/round1/reasoning.md",
    ...     ),
    ...     output_path="nk_records/task_072.json",
    ... )
    >>>
    >>> # depth-3: three rounds of Self-Debug failure
    >>> deep_nk = curator.produce_deep(
    ...     task_id="072",
    ...     task_inst="...",
    ...     rounds=[round1_arts, round2_arts, round3_arts],  # 3 FailureArtifacts
    ...     output_path="nk_records/task_072_deep.json",
    ... )

================================================================
CLI use
================================================================

Produce one depth-1 NK for one task::

    python nk_curator.py depth1 \\
        --task-id 072 \\
        --task-inst-file task_072_inst.txt \\
        --round-dir runs/round1/task_072 \\
        --output nk_records/task_072.json

Produce one depth-3 deep NK::

    python nk_curator.py deep \\
        --task-id 072 \\
        --task-inst-file task_072_inst.txt \\
        --round-dir runs/round1/task_072 \\
        --round-dir runs/round2_B2/task_072 \\
        --round-dir runs/round3_B2/task_072 \\
        --output nk_records/task_072_deep.json

The CLI is a thin wrapper; for real reproduction flows, prefer the
programmatic API.

================================================================
Schema
================================================================

Depth-1 NK (``SCHEMA_BASE``)::

    {
      "task_id": "072",
      "attempted_route": "<= 200 chars; specific method + library + parameters",
      "observation": "<= 200 chars; failure signature",
      "failure": {
        "layer": "implementation_failure | communication_failure | method_failure",
        "scope": "local_failure | regime_bound_failure | general_failure",
        "degree": "contradicted | partial | inconclusive | unstable | artifact_driven | overclaimed",
        "recommended_action": "retry | change_method | narrow_claim | abandon_route",
        "risk": "low_risk_omission | medium_risk_drift | high_risk_false_progress"
      },
      "rationale": "<= 300 chars; mechanism-level explanation",
      "recommended_alternative": "<= 300 chars; one specific concrete fix"
    }

Depth-N NK adds (``SCHEMA_DEEP``)::

    {
      ...all base fields...,
      "depth": <N>,
      "rounds_summary": [
        {"round": 1, "attempted_route": "...", "observation": "..."},
        ...one per round...
      ],
      "ruled_out_routes": ["...", "...", "..."],
      "synthesised_diagnosis": "<= 400 chars; coherent mechanism across all rounds"
    }
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
from dataclasses import dataclass, asdict, field
from typing import Optional

HERE = pathlib.Path(__file__).resolve().parent

# Reuse the dispatcher's tool-use loop. nk_curator is the high-level
# "what" (NK schema + prompt + validation); dispatch_subagent is the
# low-level "how" (API loop + tool plumbing).
sys.path.insert(0, str(HERE / "scripts"))
from dispatch_subagent import run_subagent, MODEL_ALIASES


# ============================================================
# Schema constants
# ============================================================

SCHEMA_BASE_FIELDS = (
    "task_id", "attempted_route", "observation", "failure",
    "rationale", "recommended_alternative",
)
SCHEMA_DEEP_EXTRA = (
    "depth", "rounds_summary", "ruled_out_routes",
    "synthesised_diagnosis",
)
FAILURE_SUBFIELDS = (
    "layer", "scope", "degree", "recommended_action", "risk",
)
LAYERS = ("implementation_failure", "communication_failure", "method_failure")
SCOPES = ("local_failure", "regime_bound_failure", "general_failure")
DEGREES = ("contradicted", "partial", "inconclusive", "unstable",
           "artifact_driven", "overclaimed")
RECOMMENDED_ACTIONS = ("retry", "change_method", "narrow_claim",
                       "abandon_route")
RISKS = ("low_risk_omission", "medium_risk_drift",
         "high_risk_false_progress")


def validate_nk(nk: dict, depth: int = 1) -> list[str]:
    """Return a list of schema violations (empty list = valid).

    For depth=1: requires the 6 base fields (including ``attempted_route``
    and ``observation`` at the top level).

    For depth>=2: requires the 4 deep-extension fields plus base fields
    EXCEPT ``attempted_route`` / ``observation`` (those move into the
    per-round entries inside ``rounds_summary``).
    """
    issues: list[str] = []

    if depth == 1:
        required_base = SCHEMA_BASE_FIELDS
    else:
        # depth >= 2: drop top-level attempted_route + observation
        # (they exist per-round inside rounds_summary)
        required_base = tuple(
            f for f in SCHEMA_BASE_FIELDS
            if f not in ("attempted_route", "observation")
        )
    for fld in required_base:
        if fld not in nk:
            issues.append(f"missing base field: {fld}")

    f = nk.get("failure", {})
    if isinstance(f, dict):
        for sub in FAILURE_SUBFIELDS:
            if sub not in f:
                issues.append(f"failure.{sub} missing")
        if f.get("layer") not in LAYERS:
            issues.append(f"failure.layer not in {LAYERS}: {f.get('layer')!r}")
        if f.get("scope") not in SCOPES:
            issues.append(f"failure.scope not in {SCOPES}")
        if f.get("degree") not in DEGREES:
            issues.append(f"failure.degree not in {DEGREES}")
        if f.get("recommended_action") not in RECOMMENDED_ACTIONS:
            issues.append(
                f"failure.recommended_action not in {RECOMMENDED_ACTIONS}"
            )
        if f.get("risk") not in RISKS:
            issues.append(f"failure.risk not in {RISKS}")
    else:
        issues.append("failure block is not a dict")

    if depth >= 2:
        for fld in SCHEMA_DEEP_EXTRA:
            if fld not in nk:
                issues.append(f"missing deep field: {fld}")
        if nk.get("depth") != depth:
            issues.append(f"depth field {nk.get('depth')!r} != expected {depth}")
        rs = nk.get("rounds_summary")
        if not isinstance(rs, list) or len(rs) != depth:
            issues.append(
                f"rounds_summary should be a list of {depth} entries"
            )
        else:
            for i, r in enumerate(rs):
                if not isinstance(r, dict):
                    issues.append(f"rounds_summary[{i}] not a dict")
                    continue
                for sub in ("attempted_route", "observation"):
                    if sub not in r:
                        issues.append(f"rounds_summary[{i}].{sub} missing")
        rr = nk.get("ruled_out_routes")
        if not isinstance(rr, list) or len(rr) < 2:
            issues.append("ruled_out_routes should be a list of >= 2 entries")
    return issues


# ============================================================
# Failure artifact bundle
# ============================================================

@dataclass
class FailureArtifacts:
    """The four-file bundle a curator reads for one failed round.

    For depth-1 curation: pass one of these.
    For depth-N curation: pass a list of N of these.

    Fields may be set to None or to a non-existent path; the curator's
    prompt template flags ``eval_log`` as ``ABSENT`` if it doesn't exist
    (the common case for round-1 attempts that crash before the
    evaluator runs).
    """
    candidate: str    # candidate.py path
    exec_log: str     # exec.log path
    reasoning: str    # reasoning.md path
    eval_log: Optional[str] = None  # eval.log path; None if absent

    def files(self) -> list[str]:
        out = [self.candidate, self.exec_log, self.reasoning]
        if self.eval_log is not None and pathlib.Path(self.eval_log).exists():
            out.append(self.eval_log)
        return out


# ============================================================
# Prompt templates
# ============================================================

class CuratorPrompt:
    """Wraps a curator prompt template with substitution + I/O hooks.

    The canonical template lives at the top of ``section3_reproduce/``
    as ``curator_prompt.md``. Two documented modifications live in
    ``prompts/`` with self-describing filenames:

    - ``curator_prompt.md`` (canonical, top-level) — multi-round
      distillation; produces depth-N NK with cross-round fields.
    - ``prompts/curator_prompt__single_round_simpler_schema.md`` —
      restrict input to 1 round; drop cross-round output fields.
    - ``prompts/curator_prompt__chain_with_prior_nk.md`` —
      add prior NK to input; add ``relationship_to_round1`` to output.

    Reviewers and downstream callers can override by passing
    ``base_dir=...`` (the directory containing ``curator_prompt.md``
    and ``prompts/``) or by constructing ``CuratorPrompt`` directly
    with any template path.
    """

    CANONICAL_FILE = "curator_prompt.md"  # at base_dir
    SINGLE_ROUND_FILE = "prompts/curator_prompt__single_round_simpler_schema.md"
    CHAIN_FILE = "prompts/curator_prompt__chain_with_prior_nk.md"
    BODY_MARKER = "# Materialized prompt (template body)"

    def __init__(self, template_path: pathlib.Path):
        self.template_path = pathlib.Path(template_path)
        raw = self.template_path.read_text()
        if self.BODY_MARKER in raw:
            self.body = raw.split(self.BODY_MARKER, 1)[1].lstrip()
        else:
            self.body = raw

    def materialize(self, **subs: str) -> str:
        """Apply ``{KEY}`` substitutions to the prompt body."""
        out = self.body
        for k, v in subs.items():
            out = out.replace("{" + k + "}", str(v))
        return out

    @classmethod
    def canonical(cls, base_dir: pathlib.Path) -> "CuratorPrompt":
        """The most general (multi-round distillation) template."""
        return cls(base_dir / cls.CANONICAL_FILE)

    @classmethod
    def single_round_variant(cls, base_dir: pathlib.Path) -> "CuratorPrompt":
        """The single-round, simpler-schema variant (depth-1)."""
        return cls(base_dir / cls.SINGLE_ROUND_FILE)

    @classmethod
    def chain_variant(cls, base_dir: pathlib.Path) -> "CuratorPrompt":
        """The chain-with-prior-NK variant (r2 ablation)."""
        return cls(base_dir / cls.CHAIN_FILE)

    # ---- Back-compat aliases (kept so older callers keep working) ----

    @classmethod
    def for_depth1(cls, base_dir: pathlib.Path) -> "CuratorPrompt":
        return cls.single_round_variant(base_dir)

    @classmethod
    def for_deep(cls, base_dir: pathlib.Path) -> "CuratorPrompt":
        return cls.canonical(base_dir)


# ============================================================
# Curator
# ============================================================

@dataclass
class CurationResult:
    """Outcome of one curator dispatch."""
    task_id: str
    depth: int
    output_path: str
    nk: dict
    schema_issues: list[str]
    dispatch: dict  # token usage etc. from dispatch_subagent.run_subagent


class NKCurator:
    """Produce structured NK records from failure artifacts.

    Parameters
    ----------
    model : str
        Claude model name (use one of ``MODEL_ALIASES`` keys: 'sonnet',
        'haiku', 'opus') or a full model id like 'claude-sonnet-4-5'.
    prompt_dir : pathlib.Path, optional
        Directory containing curator prompt templates. Defaults to
        ``<repo>/prompts``.
    """

    def __init__(self, model: str = "sonnet",
                 base_dir: Optional[pathlib.Path] = None):
        """``base_dir`` is the directory containing ``curator_prompt.md``
        (the canonical template) and a ``prompts/`` subdirectory with
        the two variant templates. Defaults to ``section3_reproduce/``
        (the directory holding this module)."""
        self.model = MODEL_ALIASES.get(model, model)
        self.base_dir = base_dir or HERE
        if not (self.base_dir / CuratorPrompt.CANONICAL_FILE).exists():
            raise FileNotFoundError(
                f"canonical prompt not found at "
                f"{self.base_dir / CuratorPrompt.CANONICAL_FILE}"
            )

    # ---------- depth-1 ----------

    def produce_depth1(
        self,
        task_id: str,
        task_inst: str,
        round_artifacts: FailureArtifacts,
        output_path: pathlib.Path,
        round_dir: Optional[pathlib.Path] = None,
    ) -> CurationResult:
        """Curate one round of failure into a depth-1 NK record.

        round_dir is the directory containing the artifacts (only used
        to substitute ``{ROUND1_DIR}`` in the prompt). If not given,
        derived from ``round_artifacts.candidate``'s parent.
        """
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if round_dir is None:
            round_dir = pathlib.Path(round_artifacts.candidate).parent

        eval_present = (
            round_artifacts.eval_log is not None and
            pathlib.Path(round_artifacts.eval_log).exists()
        )
        eval_note = ("Present — read it." if eval_present
                     else "ABSENT — exec crashed before evaluator ran.")

        prompt = CuratorPrompt.single_round_variant(self.base_dir).materialize(
            TASK_ID=task_id,
            TASK_INST=task_inst,
            ROUND1_DIR=str(round_dir),
            OUTPUT_NK_PATH=str(output_path),
            EVAL_LOG_STATUS=eval_note,
        )

        read_allowlist = {str(pathlib.Path(p).resolve())
                          for p in round_artifacts.files()}
        write_allowlist = {str(output_path.resolve())}

        result = run_subagent(prompt, self.model,
                              read_allowlist, write_allowlist)

        nk = json.load(open(output_path))
        issues = validate_nk(nk, depth=1)
        return CurationResult(
            task_id=task_id, depth=1, output_path=str(output_path),
            nk=nk, schema_issues=issues, dispatch=result,
        )

    # ---------- depth-N (deep) ----------

    def produce_deep(
        self,
        task_id: str,
        task_inst: str,
        rounds: list[FailureArtifacts],
        output_path: pathlib.Path,
        round_dirs: Optional[list[pathlib.Path]] = None,
    ) -> CurationResult:
        """Curate N >= 2 rounds of failure into a depth-N deep NK record.

        ``rounds`` is a list of FailureArtifacts, one per round, ordered
        round-1, round-2, .... ``round_dirs`` (optional) overrides where
        the prompt template thinks each round's artifacts live; if not
        given, derived from each round's candidate path's parent.

        Currently the bundled depth-N template targets N=3 specifically
        (that is what the paper experiment used). For N != 3, the
        recommended_alternative field's quality is not validated.
        """
        if len(rounds) < 2:
            raise ValueError("produce_deep requires >= 2 rounds; "
                             "for 1 round use produce_depth1")
        depth = len(rounds)

        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if round_dirs is None:
            round_dirs = [pathlib.Path(r.candidate).parent for r in rounds]

        def eval_status(art: FailureArtifacts) -> str:
            present = (art.eval_log is not None
                       and pathlib.Path(art.eval_log).exists())
            return "Present" if present else "ABSENT"

        subs = {
            "TASK_ID": task_id,
            "TASK_INST": task_inst,
            "OUTPUT_NK_PATH": str(output_path),
        }
        if depth >= 3:
            subs["ROUND1_DIR"] = str(round_dirs[0])
            subs["ROUND2_DIR"] = str(round_dirs[1])
            subs["ROUND3_DIR"] = str(round_dirs[2])
            subs["ROUND2_EVAL_PRESENT"] = eval_status(rounds[1])
            subs["ROUND3_EVAL_PRESENT"] = eval_status(rounds[2])

        prompt = CuratorPrompt.canonical(self.base_dir).materialize(**subs)

        read_allowlist = set()
        for r in rounds:
            read_allowlist.update(str(pathlib.Path(p).resolve())
                                  for p in r.files())
        write_allowlist = {str(output_path.resolve())}

        result = run_subagent(prompt, self.model,
                              read_allowlist, write_allowlist)

        nk = json.load(open(output_path))
        issues = validate_nk(nk, depth=depth)
        return CurationResult(
            task_id=task_id, depth=depth, output_path=str(output_path),
            nk=nk, schema_issues=issues, dispatch=result,
        )


# ============================================================
# CLI
# ============================================================

def _load_text(path: pathlib.Path) -> str:
    return pathlib.Path(path).read_text()


def _from_round_dir(d: pathlib.Path) -> FailureArtifacts:
    d = pathlib.Path(d)
    return FailureArtifacts(
        candidate=str(d / "candidate.py"),
        exec_log=str(d / "exec.log"),
        reasoning=str(d / "reasoning.md"),
        eval_log=str(d / "eval.log") if (d / "eval.log").exists() else None,
    )


def _cmd_depth1(args):
    curator = NKCurator(model=args.model)
    res = curator.produce_depth1(
        task_id=args.task_id,
        task_inst=_load_text(args.task_inst_file),
        round_artifacts=_from_round_dir(args.round_dir[0]),
        output_path=args.output,
        round_dir=args.round_dir[0],
    )
    _print_summary(res)


def _cmd_deep(args):
    if len(args.round_dir) < 2:
        sys.exit("`deep` requires --round-dir at least twice")
    curator = NKCurator(model=args.model)
    rounds = [_from_round_dir(d) for d in args.round_dir]
    res = curator.produce_deep(
        task_id=args.task_id,
        task_inst=_load_text(args.task_inst_file),
        rounds=rounds,
        output_path=args.output,
        round_dirs=[pathlib.Path(d) for d in args.round_dir],
    )
    _print_summary(res)


def _print_summary(res: CurationResult):
    d = res.dispatch
    print(f"\n NK record written: {res.output_path}")
    print(f"   depth          = {res.depth}")
    print(f"   tokens         = {d['total_tokens']}")
    print(f"   tool_uses      = {d['tool_uses']}")
    print(f"   duration       = {d['duration_sec']}s")
    print(f"   stop_reason    = {d['stop_reason']}")
    if res.schema_issues:
        print(f"   schema issues  = {len(res.schema_issues)}:")
        for i in res.schema_issues:
            print(f"     - {i}")
    else:
        print(f"   schema valid   ✓")
    print(f"\n   recommended_alternative (preview):")
    print(f"     {res.nk.get('recommended_alternative', '<missing>')[:200]}")


def main():
    ap = argparse.ArgumentParser(
        description="Negative Knowledge curator. Produces structured NK "
                    "records from failed attempts via the Anthropic API."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--task-id", required=True, help="3-digit task id")
    common.add_argument("--task-inst-file", type=pathlib.Path, required=True,
                        help="Plain-text file with task instruction")
    common.add_argument("--round-dir", type=pathlib.Path, action="append",
                        required=True,
                        help="Round artifact dir (repeat for deep). Must "
                             "contain candidate.py, exec.log, reasoning.md, "
                             "and optionally eval.log.")
    common.add_argument("--output", required=True, type=pathlib.Path,
                        help="Path to write the NK JSON file.")
    common.add_argument("--model", default="sonnet",
                        help="Claude model alias or full id (default: sonnet)")

    d1 = sub.add_parser("depth1", parents=[common],
                        help="Produce depth-1 NK from one failed round.")
    d1.set_defaults(func=_cmd_depth1)

    dN = sub.add_parser("deep", parents=[common],
                        help="Produce depth-N NK from N>=2 failed rounds.")
    dN.set_defaults(func=_cmd_deep)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
