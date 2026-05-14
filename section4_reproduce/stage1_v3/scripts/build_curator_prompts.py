#!/usr/bin/env python3
"""Generate 20 curator prompts: 5 programs x (3 per-round + 1 deep)."""
import pathlib

ROOT = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3")
NK_DIR = ROOT / "nk_records"
NK_DIR.mkdir(exist_ok=True)

PER_ROUND_TPL = (ROOT / "curator_prompts" / "per_round_template.md").read_text()
DEEP_TPL = (ROOT / "curator_prompts" / "deep_template.md").read_text()

PROGRAMS = {
    "BKdV-S1": "What numerical methods stably integrate BKdV at amp [1,3] for T=10? Find at least one working stack and characterize at least two failure modes.",
    "BKdV-S2": "What conserved or near-conserved quantities exist in BKdV time evolution? Which are exact physical conservation laws, which numerical artifacts, which appear conserved but slowly drift?",
    "BKdV-S3": "From which IC families does BKdV produce coherent (long-lived localized) structures, and from which incoherent radiation? Is there a phase boundary?",
    "BKdV-S4": "How sensitive is BKdV long-time behavior to numerical resolution (dt, Nx, hyperviscosity)? Is there a regime where doubling resolution changes the qualitative answer?",
    "BKdV-S5": "Does BKdV exhibit modulational-instability-like response of a Gardner-soliton-like state on the m=0 reduction? Characterize which perturbations grow, at what rate, into what late-time state.",
}

count = 0
for prog_id, research_q in PROGRAMS.items():
    program_dir = ROOT / "runs" / prog_id
    out_dir = ROOT / "curator_prompts" / "generated"
    out_dir.mkdir(exist_ok=True)

    # 3 per-round prompts
    for r in [1, 2, 3]:
        round_dir = program_dir / f"round{r}"
        text = (PER_ROUND_TPL
                .replace("{program_id}", prog_id)
                .replace("{research_question}", research_q)
                .replace("{round_num}", str(r))
                .replace("{round_dir}", str(round_dir))
                .replace("{program_dir}", str(program_dir))
                .replace("{nk_records_dir}", str(NK_DIR)))
        out = out_dir / f"{prog_id}_r{r}.md"
        out.write_text(text)
        count += 1

    # 1 deep prompt
    text = (DEEP_TPL
            .replace("{program_id}", prog_id)
            .replace("{research_question}", research_q)
            .replace("{program_dir}", str(program_dir))
            .replace("{nk_records_dir}", str(NK_DIR)))
    out = out_dir / f"{prog_id}_deep.md"
    out.write_text(text)
    count += 1

print(f"wrote {count} curator prompts (5 programs x (3 per-round + 1 deep))")
