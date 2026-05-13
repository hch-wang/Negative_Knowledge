#!/usr/bin/env python3
"""Write dispatch_log.jsonl from the 24 curator agent responses captured
in the conversation context."""
import json
import pathlib

OUT = pathlib.Path(
    "/Users/dietcoke/Documents/Project/00-simulation_software/"
    "paper/Negative_Knowledge/section3/04_outputs/dispatch_log.jsonl"
)
DISPATCHED_AT = "2026-05-13T08:31:17Z"
COMPLETED_AT = "2026-05-13T08:34:00Z"  # approximate; all returned within ~3 min

RECORDS = [
    ("002", "a9b29b9f6399d8e01", "The root cause is that `shap` is not installed in the execution environment, so the script crashed at `import shap` before any feature generation or model training could begin.", 17740, 5, 21128),
    ("003", "a630b6ea5f5d37e57", "The root cause is that `StrToComposition.featurize_dataframe` was left at its default `n_jobs` (multi-process), so Python's fork-based multiprocessing re-imported the top-level script in each worker, recursively triggering another `featurize_dataframe` call and spawning an unbounded cascade of worker processes until the 180s hard timeout killed the process with SIGKILL (exit_code=-9).", 20420, 9, 65112),
    ("005", "a94c4369c46107a25", "The root cause is that the agent output hard binary labels (0/1 integers) via `predict()` instead of continuous predicted probabilities via `predict_proba()[:,1]`, causing the evaluator's numerical comparison against the true continuous `Signal-inhibition` values to fail completely despite the file being correctly formatted and findable.", 18203, 7, 51854),
    ("012", "a47a4e108ed0f348d", "The root cause is that the AAC+dipeptide protein representation discards all positional and structural binding-site information, so the Random Forest cannot learn the affinity differences that determine the correct drug ranking — the script ran cleanly and produced a file, but the ranking is numerically wrong.", 23355, 7, 45497),
    ("015", "af97134901c2c1e96", "The root cause is a column name mismatch: the script saved predicted probabilities under the column name `probability`, but the evaluator required the column to be named `Y`, causing a `KeyError` that crashed evaluation despite the model running correctly.", 20558, 7, 32369),
    ("018", "ab257cfd5d50b5d6e", "The root cause is a pandas index mismatch: the script called `reset_index(drop=True)` on each subset before writing, so the output CSVs carry index 0..N-1, while the evaluator's gold DataFrame retains the original CSV row indices — causing `Series.__eq__` to raise `ValueError: Can only compare identically-labeled Series objects` instead of performing an element-wise comparison.", 21330, 7, 32179),
    ("021", "a416b862fb1234645", "The root cause is that `gpd.clip` called shapely's intersection on geometries with topological self-conflicts introduced during the buffer-then-dissolve pipeline, and the script never applied a geometry repair step (such as `buffer(0)`) before the clip operation.", 17986, 5, 28539),
    ("022", "a80144c3aadb46389", "The root cause is that the agent correctly filtered the data but then dropped the `Classification` and `Organism` columns it had temporarily joined from `protein_set` before saving, producing a pickle whose schema is missing those columns that the ground-truth expects — causing a 0/336 score despite logically correct filtering.", 30730, 13, 71882),
    ("026", "ac9539a25eb2f187e", "The root cause was that the agent passed `return_atoms=False` to `prolif.Fingerprint.to_dataframe()`, a keyword argument that does not exist in the installed ProLIF version, causing a `TypeError` even though the fingerprint computation itself completed successfully for all 10 frames.", 18739, 6, 26238),
    ("029", "a9271e0a45b19a3ff", "The root cause is that the agent hardcoded the column name `'EDA_SCR_Peaks'` without verifying what `nk.eda_process()` actually returns; the correct SCR peak locations are stored under a different key (likely via `eda_info['EDA_Peaks']`), causing an immediate `KeyError` crash before any output was produced.", 18773, 6, 26951),
    ("034", "a4cf504faaee0a5ac", "The root cause is a NumPy 2.0 API incompatibility: the installed NeuroKit2 calls the removed `np.trapz` function inside `hrv_frequency`, crashing immediately, so the frequency-domain HRV computation never completes.", 17912, 6, 27113),
    ("035", "ac8db8f0c061586a1", "The root cause is that the agent called `nk.rsp_rate()` with a `desired_length` keyword argument that does not exist in the installed version of NeuroKit2, causing an immediate `TypeError` before any signal processing or output could occur.", 17289, 5, 22442),
    ("037", "adcfa525a9a58b54f", "The root cause was that the agent hardcoded EEG column names (\"TP9\", \"AF7\", \"AF8\", \"TP10\") based on domain assumptions without first inspecting the actual sheet's column names, causing an immediate KeyError since the MIST3 sheet uses different column labels.", 18256, 5, 31232),
    ("044", "afe5eb886f9e08f44", "The root cause is a missing required positional argument: `predict_pipeline_acceleration` requires `sampling_rate` but the agent called it with only the acceleration DataFrame, causing an immediate `TypeError` crash before any sleep endpoint computation could occur.", 17863, 5, 29194),
    ("058", "abf83e3ec342e001c", "The root cause is that the heuristic column-name detection (`detect_task_col`/`detect_pred_col`) found no matches in the actual model CSVs, producing zero fit counts for every model and every rule, causing the script to silently assign all 139 participants to \"Unknown\" and write a trivially wrong single-row output.", 20939, 6, 32822),
    ("060", "af317961c249b5ec0", "The root cause is a communication failure: the agent produced a valid CSV with self-invented column names and an improvised NVC rule-application mechanism, but the evaluator expected a specific output schema that the script never matched, resulting in a score of 0 despite clean execution.", 20256, 7, 35536),
    ("067", "a2c624420a7e75bed", "The root cause is a dimension mismatch: the agent constructed a 9-element response-vocabulary count vector from the CSV but compared it against the 1152-element flattened JNMF W matrix, which encodes a (latent_factors × syllogisms) structure — the two vectors must be in the same representational space before cosine similarity can be applied.", 18661, 6, 30319),
    ("071", "a7e594ef5f2b5e30c", "The root cause is that the agent hard-coded EEG array shape assumptions in comments and derived `n_features` from the training array's dimensions, then attempted to reshape the test array using those dimensions without verifying compatibility — when the actual file shapes differed, the reshape at line 23 raised a `ValueError`.", 18634, 5, 40415),
    ("072", "a5b3488c0006468d2", "The root cause is a dimension-order mismatch: the agent assumed the `.npy` files were shaped `(samples, channels, timepoints)` but they are actually `(channels, samples, timepoints)`, so the per-channel normalization statistics computed from `X_train` were incompatible shapes for broadcasting against `X_test`.", 20310, 5, 29306),
    ("078", "a86dabaff6fbb7031", "The root cause is that amino acid composition features are position-blind and cannot encode the local structural/thermodynamic context that drives deltaTm changes from point mutations, making the MLPRegressor produce predictions with MAE ~67°C — orders of magnitude worse than acceptable.", 19664, 6, 29696),
    ("085", "af2d3ad76bd9eb931", "The root cause is a communication failure: `biopsykit.saliva.standard_features()` produced a DataFrame whose column names did not include the bare string `'argmax'` that the evaluator looked up, causing a `KeyError` at evaluation time despite the script completing without errors.", 17496, 7, 33982),
    ("087", "aea93201fbab3a5eb", "The root cause is that the script's output column names (`year`, `actual_temp`, `predicted_temp`) did not match the benchmark evaluator's expected schema, causing a score of 0 despite the script running correctly and producing 240 rows.", 18006, 7, 34529),
    ("097", "aeddab7f0edac4d49", "The root cause is that `deepchem.models.CGCNNModel` has a hard dependency on the `dgl` (Deep Graph Library) package, which was not installed in the virtual environment, causing an `ImportError` before any training could begin.", 18206, 5, 22442),
    ("101", "a111f0d446b6d4af4", "Root cause: the matbench dataset file is stored as Python pickle (protocol 5, magic `b'\\x80\\x05'`), but the agent loaded it with `pd.read_json(..., compression=\"gzip\")`, which immediately raised `gzip.BadGzipFile` — no ML code ever ran.", 18364, 6, 28717),
]

with OUT.open("w") as f:
    for tid, agent_id, msg, toks, tu, dur in RECORDS:
        rec = {
            "task_id": tid,
            "agent_id": agent_id,
            "return_message": msg,
            "tokens": toks,
            "tool_uses": tu,
            "duration_ms": dur,
            "dispatched_at_utc": DISPATCHED_AT,
            "completed_at_utc": COMPLETED_AT,
        }
        f.write(json.dumps(rec) + "\n")

print(f"wrote {len(RECORDS)} dispatch records to {OUT}")
