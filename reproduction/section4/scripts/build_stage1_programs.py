#!/usr/bin/env python3
"""Generate 7 BKdV-S program prompts from the master template."""
from _paths import BKDV_PROGRAMS, PROMPTS, PY, RUNS

TPL = (PROMPTS / "stage1_program_template.md").read_text()
VENV_PY = str(PY)

PROGRAMS = {
    "BKdV-S1": {
        "research_question": "What numerical methods stably integrate BKdV at amp ∈ [1, 3] for T = 10? Find at least one working stack and characterize at least two failure modes (specific methods + their failure signatures).",
        "program_specific_notes": """This program EXPLORES method choices — unlike other BKdV-S programs where you use the pre-validated stack, here you may iterate on the solver itself.
- E1: try the simplest method you'd reach for (e.g. Fourier spectral + RK4 + no dealiasing) on a moderate IC (v0 = 1.5 sech²(x+5), u0 = v0²/2). Document failure mode.
- E2: change ONE component based on F1
- E3: change ONE more component based on F2
A "success" outcome for the program is identifying which components are necessary; "failure" outcomes (methods that didn't work) are equally valuable for the bank."""
    },
    "BKdV-S2": {
        "research_question": "What conserved or near-conserved quantities exist in BKdV time evolution? Which are exact physical conservation laws, which are numerical artifacts, and which appear conserved but actually drift slowly?",
        "program_specific_notes": """Use the pre-validated solver stack. Vary the diagnostic, not the method.
Candidates to test: ∫u dx, ∫v dx, ∫uv dx, ∫(½u² + ½v² + ½v_x²) dx, ∫m² dx (where m=u-v²/2).
- E1: run long-time (T=20) baseline with v0 = 1.5 sech²(x+5), u0 = 0; track ALL candidates per timestep.
- E2: change IC type (e.g. random small-amplitude or sinusoidal) to see which quantities remain conserved IC-invariantly vs which only happen to be conserved for the specific IC.
- E3: numerical artifact control — change dt by 5x or change Nx, see which quantities change. Anything that depends on dt is artifact.

Trivial-findings expected: "mass is conserved because the equation is divergence form" is true-by-construction = trivial."""
    },
    "BKdV-S3": {
        "research_question": "From which IC families does BKdV produce coherent (long-lived localized) structures, and from which does it produce incoherent radiation? Is there a phase boundary?",
        "program_specific_notes": """Use pre-validated solver stack.
- E1: scan ≥3 IC types at moderate amplitude — single Gaussian / sech² / random-noise / two-pulse / sinusoidal. Identify which become coherent late-time (peak count remains small, peaks have v-amp ≥ 0.5).
- E2: based on F1's "coherent IC family", scan amplitude to find threshold below which coherent structure fails to form.
- E3: probe between coherent and incoherent regimes by varying ONE parameter (e.g. IC width, IC noise level) to look for phase boundary.

Trivial-findings expected: "IC with amp=0 produces no coherent structure" is trivial (no dynamics)."""
    },
    "BKdV-S4": {
        "research_question": "How sensitive is BKdV long-time behavior to numerical resolution (dt, Nx, hyperviscosity coefficient)? Is there a regime where doubling resolution changes the qualitative answer (vs only quantitative)?",
        "program_specific_notes": """Use pre-validated solver stack. Vary numerical parameters, not physics.
- E1: baseline at (dt=5e-4, Nx=256, hyperviscosity ν_h=1e-22) with v0=1.5 sech²(x+5), u0=v0²/2; T=10; record diagnostics.
- E2: change ONE parameter (e.g. dt → 1e-4 or Nx → 512 or ν_h → 1e-18). Compare diagnostics.
- E3: change a DIFFERENT parameter (the one not changed in E2). Compare.

Key output: which parameters are robust (change → < 5% diagnostic shift) and which are sensitive (change → qualitative shift). Sensitive parameters → numerical-artifact risk for any claim relying on them.

Trivial-findings expected: "dt → very small gives same answer" is trivial if dt is already in converged regime."""
    },
    "BKdV-S5": {
        "research_question": "Does BKdV exhibit modulational instability of known stable structures (e.g. Gardner soliton in the m=0 reduction)? If so, characterize: which perturbations grow, at what rate, into what late-time state.",
        "program_specific_notes": """Use pre-validated solver stack.
- E1: baseline — Gardner soliton IC (v = a sech²(x+5) with u = v²/2, so m₀ ≈ 0; choose a such that this is an approximate Gardner soliton). Run T=15. Does it propagate stably?
- E2: perturb the baseline with a small structured perturbation (e.g. δv = 0.05 sin(k₀ x) for some chosen k₀). Does it grow? If yes, characterize growth rate.
- E3: perturb with a different structure (different k₀, or random noise of same L²-norm) to see if growth is k-selective or general.

A clean negative answer ("no observable instability up to T=15 across tested perturbations") is also valuable.

Trivial-findings expected: "constant zero solution is stable" is trivial."""
    },
    "BKdV-S6": {
        "research_question": "Under the standard pre-validated stack with no explicit u-side viscosity, does the u-equation remain bounded for bore-like moderately-amplitude ICs? If not, what minimum explicit u-side dissipation restores boundedness without distorting v?",
        "program_specific_notes": """Use the fixed stress IC across rounds:
- v(x,0) = 1.5 sech²(x+5)
- u(x,0) = 1.5 (1 - tanh(x/0.5)) / 2
- periodic x ∈ [-15,15], Nx=256, T=6.

This program stresses Burgers self-flux under coupling.
- E1: pre-validated spectral + 2/3 dealiasing + RK4 stack with NO u-viscosity/filter. Track |u|max(t), Gibbs oscillations, and boundedness.
- E2: add one component only: small linear viscosity epsilon*u_xx on u, epsilon=1e-4. Keep every other parameter fixed.
- E3: based on F2, either increase epsilon or switch to k^8 hyperviscosity; quantify the smallest dissipation that keeps u bounded.

The key downstream lesson should distinguish aliasing control from real shock regularisation: dealiasing prevents spectral wraparound, but it does not dissipate intrinsic high-k content from a developing bore."""
    },
    "BKdV-S7": {
        "research_question": "Find an IC that is stable in Gardner-only evolution but unstable in full BKdV when initialized with u0 = v0^2/2. Characterize whether m=0 drifts, which modes amplify, and on what timescale.",
        "program_specific_notes": """Compare a Gardner-only solver against the full BKdV solver with identical numerical parameters:
- v(x,0) = A sech²(x+5), A=1.5
- Gardner: evolve v only.
- BKdV: use the same v plus u(x,0)=v(x,0)^2/2, so m0=0.
- periodic x ∈ [-15,15], Nx=256, T=10.

- E1: Gardner-only baseline. Verify whether the profile remains a single coherent peak with amplitude preserved.
- E2: full BKdV with matching IC. Track ||m||_L2(t), v_max(t), u_max(t), and L2 distance between BKdV v and Gardner v.
- E3: either scan a nearby amplitude threshold or track which spectral modes of m first grow.

Tie the mechanism back to the m=0 non-invariance identity from BKdV-S5: a Gardner-stable profile is not automatically BKdV-stable."""
    },
}

for prog_id in BKDV_PROGRAMS:
    spec = PROGRAMS[prog_id]
    cwd = RUNS / "stage1" / prog_id
    cwd.mkdir(parents=True, exist_ok=True)
    text = (TPL
            .replace("{program_id}", prog_id)
            .replace("{research_question}", spec["research_question"])
            .replace("{program_specific_notes}", spec["program_specific_notes"])
            .replace("{cwd}", str(cwd))
            .replace("{venv_py}", VENV_PY))
    out = cwd / "prompt.md"
    out.write_text(text)
    print(f"  wrote {prog_id}/prompt.md ({len(text)} chars)")

print(f"\nbuilt {len(PROGRAMS)} program prompts")
