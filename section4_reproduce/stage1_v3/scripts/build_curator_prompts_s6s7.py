#!/usr/bin/env python3
"""Generate 8 curator prompts for new S6 and S7 programs."""
import pathlib

ROOT = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/Negative_Knowledge/section4/stage1_v3")
NK_DIR = ROOT / "nk_records"
PER_ROUND_TPL = (ROOT / "curator_prompts" / "per_round_template.md").read_text()
DEEP_TPL = (ROOT / "curator_prompts" / "deep_template.md").read_text()

PROGRAMS = {
    "BKdV-S6": "Under the standard pre-validated stack (Fourier pseudospectral + 2/3-rule dealiasing + classical RK4) with NO explicit viscosity/hyperviscosity on u, does the u-equation remain bounded for ICs that stress the Burgers self-flux (smoothed bore u + sech² v)? What minimum level of u-side dissipation is needed?",
    "BKdV-S7": "Find an IC stable under Gardner equation (the m=0 reduction of BKdV) but unstable under full BKdV when initialized at m₀=0. Characterize the breakdown mechanism quantitatively.",
}

count = 0
out_dir = ROOT / "curator_prompts" / "generated"
for prog_id, research_q in PROGRAMS.items():
    program_dir = ROOT / "runs" / prog_id

    for r in [1, 2, 3]:
        round_dir = program_dir / f"round{r}"
        text = (PER_ROUND_TPL
                .replace("{program_id}", prog_id)
                .replace("{research_question}", research_q)
                .replace("{round_num}", str(r))
                .replace("{round_dir}", str(round_dir))
                .replace("{program_dir}", str(program_dir))
                .replace("{nk_records_dir}", str(NK_DIR)))
        (out_dir / f"{prog_id}_r{r}.md").write_text(text)
        count += 1

    text = (DEEP_TPL
            .replace("{program_id}", prog_id)
            .replace("{research_question}", research_q)
            .replace("{program_dir}", str(program_dir))
            .replace("{nk_records_dir}", str(NK_DIR)))
    (out_dir / f"{prog_id}_deep.md").write_text(text)
    count += 1

print(f"wrote {count} curator prompts (2 programs × 4 each)")
