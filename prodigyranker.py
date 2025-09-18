#!/usr/bin/env python3
"""
Run prodigy on all *_prodigy.pdb files and collect results,
then create CSV summaries of binding affinities.
"""

import os
import re
import csv
import subprocess
import shutil

def unique_move(src_path, dst_dir):
    """Move src_path into dst_dir, avoid overwriting by appending suffixes."""
    os.makedirs(dst_dir, exist_ok=True)
    base = os.path.basename(src_path)
    name, ext = os.path.splitext(base)
    dst = os.path.join(dst_dir, base)
    counter = 1
    while os.path.exists(dst):
        dst = os.path.join(dst_dir, f"{name}_{counter}{ext}")
        counter += 1
    shutil.move(src_path, dst)
    return dst

def parse_affinity_from_output(file_path):
    """Extract binding affinity from a prodigy output log file."""
    pattern = re.compile(r"\[\+\+\] Predicted binding affinity \(kcal\.mol-1\):\s+(-?\d+\.\d+)")
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                return float(match.group(1))
    return None

def summarize_affinities(results_root):
    """Collect all affinities from *_output.txt and save two CSVs."""
    affinities = []  # (ligand, rank, affinity)

    for root, _, files in os.walk(results_root):
        for fname in files:
            if fname.endswith("_output.txt"):
                path = os.path.join(root, fname)

                # Example filename: LYD_1_output.txt → ligand=LYD, rank=1
                parts = fname.split("_")
                ligand = parts[0]
                rank = None
                if len(parts) > 1 and parts[1].isdigit():
                    rank = int(parts[1])

                affinity = parse_affinity_from_output(path)
                if affinity is not None:
                    affinities.append((ligand, rank, affinity, path))

    if not affinities:
        print("[WARN] No affinities found in output logs.")
        return

    # Write all_affinities.csv (unsorted)
    all_csv = os.path.join(results_root, "all_affinities.csv")
    with open(all_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Ligand", "Rank", "Affinity (kcal/mol)", "File"])
        writer.writerows(affinities)
    print(f"[INFO] Wrote {all_csv}")

    # Write ranked_affinities.csv (sorted strongest binders first)
    ranked_csv = os.path.join(results_root, "ranked_affinities.csv")
    sorted_affinities = sorted(affinities, key=lambda x: x[2])  # more negative = stronger
    with open(ranked_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Ligand", "Rank", "Affinity (kcal/mol)", "File"])
        writer.writerows(sorted_affinities)
    print(f"[INFO] Wrote {ranked_csv}")

def run_prodigy_and_collect(base_dir):
    base_dir = os.path.abspath(base_dir)
    results_root = os.path.join(base_dir, "prodigyresults")
    os.makedirs(results_root, exist_ok=True)
    print(f"[INFO] results root: {results_root}")

    # Find all *_prodigy.pdb files
    all_files = sorted(os.listdir(base_dir))
    prodigy_files = [f for f in all_files if f.endswith("_prodigy.pdb")]

    if not prodigy_files:
        print("[WARN] No *_prodigy.pdb files found in", base_dir)
        return

    processed_codes = set()

    for pdb in prodigy_files:
        pdb_path = os.path.join(base_dir, pdb)
        ligand_code = pdb.split("_", 1)[0]
        processed_codes.add(ligand_code)

        dest_folder = os.path.join(results_root, ligand_code)
        os.makedirs(dest_folder, exist_ok=True)

        print(f"\n[INFO] Processing file: {pdb}")
        print(f"[INFO] Ligand code: {ligand_code}")
        print(f"[INFO] Destination folder: {dest_folder}")

        # Snapshot of directory BEFORE running prodigy
        before = set(os.listdir(base_dir))

        # Run prodigy
        command = [
            "prodigy",
            pdb_path,
            "--contact_list",
            "--pymol_selection",
            "--selection", "A", "B,C"
        ]

        base_name = os.path.splitext(pdb)[0]  # e.g. "LYD_10_prodigy"
        output_log = os.path.join(dest_folder, f"{base_name}_output.txt")

        # Run prodigy with UTF-8 forced
        with open(output_log, "w", encoding="utf-8") as out:
            try:
                print("[INFO] Running prodigy:", " ".join(command))
                subprocess.run(
                    command,
                    check=True,
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
                print(f"[INFO] prodigy completed for {pdb}")
                print(f"[DEBUG] Log written -> {output_log}")
            except subprocess.CalledProcessError:
                print(f"[ERROR] prodigy failed for {pdb}. See {output_log} for details.")
            except FileNotFoundError:
                print("[ERROR] 'prodigy' executable not found. Make sure prodigy is on your PATH.")
                return

        # Snapshot AFTER running prodigy
        after = set(os.listdir(base_dir))
        created_files = after - before

        # Move only files belonging to this job
        for fname in sorted(os.listdir(base_dir)):
            src = os.path.join(base_dir, fname)
            if not os.path.isfile(src):
                continue

            # Rule 1: exact match of base_name + extension
            same_job = fname.startswith(base_name)

            # Rule 2: new prodigy-created files that contain base_name
            prodigy_created = fname in created_files and base_name in fname

            if same_job or prodigy_created:
                try:
                    moved_to = unique_move(src, dest_folder)
                    print(f"[MOVED] {fname} -> {moved_to}")
                except Exception as ex:
                    print(f"[ERROR] failed moving {src} -> {dest_folder}: {ex}")

    # Final summary step
    summarize_affinities(results_root)

    print("\n[INFO] All done. Processed ligand codes:", ", ".join(sorted(processed_codes)))
    print(f"[INFO] Results collected in: {results_root}")

if __name__ == "__main__":
    base = os.getcwd()
    run_prodigy_and_collect(base)
