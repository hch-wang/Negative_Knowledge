#!/usr/bin/env python3
"""Generate 28 curator prompts: 7 programs x (3 per-round + 1 deep)."""
import argparse
import pathlib

from _paths import BKDV_PROGRAMS, CURATOR_PROMPTS, RUNS, STAGE1_RUNS

PER_ROUND_TPL = (CURATOR_PROMPTS / "per_round_template.md").read_text()
DEEP_TPL = (CURATOR_PROMPTS / "deep_template.md").read_text()

PROGRAMS = {
    "BKdV-S1": "What numerical methods stably integrate BKdV at amp [1,3] for T=10? Find at least one working stack and characterize at least two failure modes.",
    "BKdV-S2": "What conserved or near-conserved quantities exist in BKdV time evolution? Which are exact physical conservation laws, which numerical artifacts, which appear conserved but slowly drift?",
    "BKdV-S3": "From which IC families does BKdV produce coherent (long-lived localized) structures, and from which incoherent radiation? Is there a phase boundary?",
    "BKdV-S4": "How sensitive is BKdV long-time behavior to numerical resolution (dt, Nx, hyperviscosity)? Is there a regime where doubling resolution changes the qualitative answer?",
    "BKdV-S5": "Does BKdV exhibit modulational-instability-like response of a Gardner-soliton-like state on the m=0 reduction? Characterize which perturbations grow, at what rate, into what late-time state.",
    "BKdV-S6": "Under the standard pre-validated stack with no explicit u-side viscosity, does the u-equation remain bounded for bore-like moderately-amplitude ICs? If not, what minimum explicit u-side dissipation restores boundedness without distorting v?",
    "BKdV-S7": "Find an IC that is stable in Gardner-only evolution but unstable in full BKdV when initialized with u0 = v0^2/2. Characterize whether m=0 drifts, which modes amplify, and on what timescale.",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", choices=["logs", "runs"], default="logs",
        help="Read Stage-1 traces from bundled logs or from REPRO_RUNS/stage1.")
    parser.add_argument(
        "--out-dir", type=pathlib.Path, default=RUNS / "curator_prompts",
        help="Directory for generated curator prompt markdown files.")
    parser.add_argument(
        "--nk-records-dir", type=pathlib.Path, default=RUNS / "nk_records",
        help="Directory curators should write JSON records to.")
    args = parser.parse_args()

    source_root = STAGE1_RUNS if args.source == "logs" else RUNS / "stage1"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.nk_records_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for prog_id in BKDV_PROGRAMS:
        research_q = PROGRAMS[prog_id]
        program_dir = source_root / prog_id

        for r in [1, 2, 3]:
            round_dir = program_dir / f"round{r}"
            text = (PER_ROUND_TPL
                    .replace("{program_id}", prog_id)
                    .replace("{research_question}", research_q)
                    .replace("{round_num}", str(r))
                    .replace("{round_dir}", str(round_dir))
                    .replace("{program_dir}", str(program_dir))
                    .replace("{nk_records_dir}", str(args.nk_records_dir)))
            out = args.out_dir / f"{prog_id}_r{r}.md"
            out.write_text(text)
            count += 1

        text = (DEEP_TPL
                .replace("{program_id}", prog_id)
                .replace("{research_question}", research_q)
                .replace("{program_dir}", str(program_dir))
                .replace("{nk_records_dir}", str(args.nk_records_dir)))
        out = args.out_dir / f"{prog_id}_deep.md"
        out.write_text(text)
        count += 1

    print(f"wrote {count} curator prompts (7 programs x (3 per-round + 1 deep)) to {args.out_dir}")


if __name__ == "__main__":
    main()
