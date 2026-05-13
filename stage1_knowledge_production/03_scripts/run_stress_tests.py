#!/usr/bin/env python3
"""Run all Stage-1 stress-test candidates and collect observed outcomes."""
import json, pathlib, subprocess, numpy as np, datetime as dt

ROOT = pathlib.Path("/stage1")
SANDBOX = ROOT / "sandboxes"
PY = "/.venv/bin/python"

def run(cmd, cwd, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -9, (e.stdout or ""), f"TIMEOUT after {timeout}s\n{e.stderr or ''}"

def analyze(arr, pde):
    """Quick diagnostic of the output array."""
    a = np.asarray(arr)
    diag = {"shape": list(a.shape), "size": int(a.size)}
    finite = np.isfinite(a)
    diag["all_finite"] = bool(finite.all())
    diag["n_nan"] = int(np.isnan(a).sum())
    diag["n_inf"] = int(np.isinf(a).sum())
    if not finite.all():
        return diag
    diag["min"] = float(a.min()); diag["max"] = float(a.max())
    diag["amplitude_range"] = float(a.max() - a.min())
    if a.ndim == 1:
        # scalar field
        # detect oscillations: max adjacent jump vs total range
        jumps = np.abs(np.diff(a))
        diag["max_jump"] = float(jumps.max())
        diag["mean_jump"] = float(jumps.mean())
        # count zero-crossings (rough oscillation indicator)
        diag["zero_crossings"] = int(np.sum(np.diff(np.sign(a - a.mean())) != 0))
        # count local maxima (peaks)
        peaks = (a[1:-1] > a[:-2]) & (a[1:-1] > a[2:])
        diag["n_local_maxima"] = int(peaks.sum())
    elif a.ndim == 2 and pde == "shallow_water":
        h = a[0]; hu = a[1]
        diag["h_min"] = float(h.min()); diag["h_max"] = float(h.max())
        diag["h_negative"] = bool((h < 0).any())
        diag["h_below_threshold"] = int((h < 1e-6).sum())
        diag["mass_h"] = float(h.sum())
        diag["max_h_jump"] = float(np.abs(np.diff(h)).max())
    return diag

all_results = []
for tid in ["A1","A2","A3","A4","A5","A6","A7","A8","A9","A10"]:
    cwd = SANDBOX / tid
    meta = json.load(open(cwd / "meta.json"))
    if not (cwd / "candidate.py").exists():
        print(f"SKIP {tid}: no candidate.py"); continue

    # cleanup
    for p in [cwd / "exec.log", cwd / "result.json", cwd / "diag.json"]:
        p.unlink(missing_ok=True)
    out_file = cwd / "pred_results" / meta["output"]
    out_file.unlink(missing_ok=True)

    print(f"=== {tid}: {meta['title']} ===", flush=True)
    t0 = dt.datetime.now()
    rc, so, se = run([PY, "candidate.py"], cwd=cwd)
    dur = (dt.datetime.now() - t0).total_seconds()
    (cwd / "exec.log").write_text(f"exit_code={rc}\nduration_sec={dur:.1f}\n--- stdout ---\n{so}\n--- stderr ---\n{se}\n")

    diag = None
    if out_file.exists():
        try:
            arr = np.load(out_file)
            diag = analyze(arr, meta["pde"])
        except Exception as e:
            diag = {"load_error": str(e)}

    result = {
        "id": tid, "title": meta["title"], "pde": meta["pde"],
        "constraint": meta["constraint"][:200],
        "exit_code": rc,
        "output_exists": out_file.exists(),
        "duration_sec": dur,
        "stderr_tail": "\n".join(se.splitlines()[-6:]) if se else "",
        "diag": diag,
        "predicted": meta["predicted"],
    }
    (cwd / "result.json").write_text(json.dumps(result, indent=2))
    all_results.append(result)

    # short summary line
    if not out_file.exists():
        status = f"NO OUTPUT (exit={rc})"
    elif diag and not diag.get("all_finite", True):
        status = f"NaN/Inf in output ({diag.get('n_nan',0)} NaN, {diag.get('n_inf',0)} Inf)"
    elif meta["pde"] == "shallow_water" and diag and diag.get("h_negative"):
        status = f"h goes negative (min h = {diag.get('h_min',0):.3f})"
    elif meta["pde"] == "shallow_water" and diag:
        status = f"OK, h in [{diag.get('h_min',0):.3f}, {diag.get('h_max',0):.3f}], mass={diag.get('mass_h',0):.3f}"
    elif diag:
        status = f"OK range [{diag.get('min',0):.3f}, {diag.get('max',0):.3f}], max_jump={diag.get('max_jump',0):.3f}, peaks={diag.get('n_local_maxima',0)}"
    else:
        status = "diagnostic failed"
    print(f"  → {status}", flush=True)

with (ROOT / "stage1_results.json").open("w") as f:
    json.dump(all_results, f, indent=2)
print(f"\nwrote stage1_results.json with {len(all_results)} entries")
