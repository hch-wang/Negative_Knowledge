"""negative_knowledge — a failure-aware shared memory layer for AutoResearch.

A *negative-knowledge (NK) record* is a bounded, typed JSON summary of a
failed attempt: what was tried, how it failed (in a closed taxonomy),
why, and what to do instead. A **curator** agent writes these records
from the artifacts a failed attempt leaves behind; a downstream
**research agent** reads them before proposing its next experiment.

Quick start
-----------
    from negative_knowledge import NKCurator, FailureArtifacts

    curator = NKCurator(model="sonnet")          # needs ANTHROPIC_API_KEY
    result = curator.produce_depth1(
        task_id="072",
        task_inst="Map Sub01 EEG signals to Sub03 ...",
        round_artifacts=FailureArtifacts(
            candidate="round1/candidate.py",
            exec_log="round1/exec.log",
            reasoning="round1/reasoning.md",
        ),
        output_path="nk_records/task_072.json",
    )
    print(result.nk["recommended_alternative"])

Validating a record needs no API key or SDK::

    from negative_knowledge import validate_nk
    issues = validate_nk(record, depth=1)   # [] == valid

See ``examples/quickstart.py`` for a runnable end-to-end demo, and the
``reproduction/`` directory for the experiments behind the paper.
"""
from .curator import (
    NKCurator,
    CurationResult,
    CuratorPrompt,
    FailureArtifacts,
    validate_nk,
    SCHEMA_BASE_FIELDS,
    SCHEMA_DEEP_EXTRA,
    FAILURE_SUBFIELDS,
    LAYERS,
    SCOPES,
    DEGREES,
    RECOMMENDED_ACTIONS,
    RISKS,
)
from .runtime import run_subagent, MODEL_ALIASES

__version__ = "0.1.0"

__all__ = [
    "NKCurator",
    "CurationResult",
    "CuratorPrompt",
    "FailureArtifacts",
    "validate_nk",
    "run_subagent",
    "MODEL_ALIASES",
    "SCHEMA_BASE_FIELDS",
    "SCHEMA_DEEP_EXTRA",
    "FAILURE_SUBFIELDS",
    "LAYERS",
    "SCOPES",
    "DEGREES",
    "RECOMMENDED_ACTIONS",
    "RISKS",
]
