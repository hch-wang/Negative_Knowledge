#!/usr/bin/env python3
"""Apply draft_section4_v3.tex into main.tex:
1. Replace current Section 4 (lines 563-818) with new main text from draft (lines 7-255).
2. Replace current bkdv-bank appendix (lines 1474-1496) with new "Stage 1 Stress-Test
   Program Catalogue" + 3 new appendix sections (eval-v2, ic-trap, agent-traces) from
   draft (lines 261-end).
"""
import pathlib

ROOT = pathlib.Path("/Users/dietcoke/Documents/Project/00-simulation_software/paper/overleaf")
main_path = ROOT / "main.tex"
draft_path = ROOT / "draft_section4_v3.tex"

main_lines = main_path.read_text().splitlines(keepends=False)
draft_lines = draft_path.read_text().splitlines(keepends=False)

# Sanity check: current main.tex section 4 boundaries
assert main_lines[562].startswith(r"\section{Case Study"), f"Line 563 expected Case Study, got: {main_lines[562][:80]}"
assert main_lines[819].startswith(r"\section{Limitations}"), f"Line 820 expected Limitations, got: {main_lines[819][:80]}"
assert main_lines[1473].startswith(r"\section{Burgers-swept-KdV Bank Composition}"), f"Line 1474 expected Bank Composition, got: {main_lines[1473][:80]}"
print("main.tex boundary checks OK")

# Find draft boundaries
APPENDIX_MARKER = "% APPENDIX ADDITIONS"
draft_section_start = None
draft_appendix_start = None
for i, line in enumerate(draft_lines):
    if draft_section_start is None and line.startswith(r"\section{Case Study"):
        draft_section_start = i
    if draft_appendix_start is None and APPENDIX_MARKER in line:
        draft_appendix_start = i

# Draft main text: from \section{Case Study...} up to (but not including) the APPENDIX marker
# The marker is preceded by a "% ====" line, so back up to skip that
appendix_marker_idx = draft_appendix_start
# Walk backward through "% =====" comment block lines
section_end = appendix_marker_idx
while section_end > 0 and (draft_lines[section_end - 1].startswith("% =") or draft_lines[section_end - 1].strip() == ""):
    section_end -= 1
draft_main = draft_lines[draft_section_start:section_end]
print(f"Draft main: {len(draft_main)} lines (draft idx {draft_section_start}..{section_end})")

# Draft appendix: everything after the marker block. Find first \section after marker
appendix_first_section = None
for i in range(draft_appendix_start, len(draft_lines)):
    if draft_lines[i].startswith(r"\section{"):
        appendix_first_section = i
        break
draft_appendix = draft_lines[appendix_first_section:]
print(f"Draft appendix: {len(draft_appendix)} lines (draft idx {appendix_first_section}..end)")

# Find end of current bkdv-bank appendix section (line 1474 to EOF, since it's the last section)
# Confirm by checking that nothing after line 1496 (where we observed bank composition ends)
# Actually let's just go to EOF and see.
print(f"main.tex total: {len(main_lines)} lines")

# Compose the new main.tex
# Part 1: lines 0..562 (up to but not including line 563 = current section 4 start)
part1 = main_lines[:562]
# Part 2: new section 4 content from draft
part2 = draft_main
# Part 3: lines 819..1473 (Limitations through end of appendix:bkdv-setup, NOT including current bkdv-bank)
part3 = main_lines[819:1473]
# Part 4: new appendix content (bkdv-bank + 3 new appendices)
part4 = draft_appendix
# (We discard lines 1474..end which were the old bkdv-bank section)

new_lines = part1 + part2 + part3 + part4

# Quick sanity printouts
print(f"\nNew main.tex composition:")
print(f"  Part 1 (preamble + sections 1-3): {len(part1)} lines")
print(f"  Part 2 (new Section 4): {len(part2)} lines")
print(f"  Part 3 (Limitations, Conclusion, appendices A-L): {len(part3)} lines")
print(f"  Part 4 (new bkdv-bank + 3 new appendices): {len(part4)} lines")
print(f"  Total: {len(new_lines)} lines (was {len(main_lines)})")

# Write
new_text = "\n".join(new_lines) + "\n"
main_path.write_text(new_text)
print(f"\nwrote {main_path}")
