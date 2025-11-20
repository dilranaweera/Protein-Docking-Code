import os
import subprocess
import csv
import glob
import re

###########################################################
# USER PARAMETERS
###########################################################

DOCKQ_BIN = "DockQ"
MODEL_DIR = "/Users/dilrana/Desktop/Kuczera/DockQ_ready"
NATIVE_FILE = "/Users/dilrana/Desktop/Kuczera/PDBfiles/1L5G.pdb"
OUTPUT_LOG_DIR = "/Users/dilrana/Desktop/Kuczera/DockQ_logs"
SUMMARY_CSV = "/Users/dilrana/Desktop/Kuczera/DockQ_summary.csv"

# DockQ options (edit freely)
DOCKQ_FLAGS = [
    "--short",
    "--n_cpu", "6",
    "--allowed_mismatches", "100",
    "--mapping", "ABC:ABC"   # model A,B,C → native A,B,C
]

###########################################################
## Run DockQ and capture output
###########################################################
def run_dockq(model_file, native_file, log_file):
    cmd = [DOCKQ_BIN, model_file, native_file] + DOCKQ_FLAGS

    with open(log_file, "w") as out:
        result = subprocess.run(
            cmd, stdout=out, stderr=subprocess.STDOUT, text=True
        )

    return result.returncode == 0

###########################################################
# Parse DockQ short output to extract numbers
###########################################################
def parse_dockq_log(log_file):
    with open(log_file, "r") as f:
        text = f.read()

    import re
    m = re.search(
        r"DockQ\s+([\d.]+)\s+iRMSD\s+([\d.]+)\s+LRMSD\s+([\d.]+)\s+fnat\s+([\d.]+)",
        text,
    )

    if not m:
        return None

    return {
        "DockQ": float(m.group(1)),
        "iRMSD": float(m.group(2)),
        "LRMSD": float(m.group(3)),
        "fnat": float(m.group(4)),
    }


###########################################################
# Main batch execution
###########################################################
def main():

    if not os.path.isdir(OUTPUT_LOG_DIR):
        os.makedirs(OUTPUT_LOG_DIR)

    rows = []

    for fname in os.listdir(MODEL_DIR):
        if not fname.endswith(".pdb"):
            continue

        model_path = os.path.join(MODEL_DIR, fname)
        ligand_name = fname.replace(".pdb", "")

        log_file = os.path.join(OUTPUT_LOG_DIR, ligand_name + ".log")

        print(f"[RUN] {ligand_name}")

        success = run_dockq(model_path, NATIVE_FILE, log_file)

        if not success:
            print(f"[ERROR] DockQ failed for {fname}")
            continue

        metrics = parse_dockq_log(log_file)
        if metrics:
            rows.append({
                "ligand": ligand_name,
                **metrics
            })

    # Save CSV summary
SUMMARY_CSV = "DockQ_summary.csv"
LOG_DIR = "path/to/dockq/logs"  # change to your log directory

rows = []
log_files = glob.glob(f"{LOG_DIR}/*.log")

for log_file in log_files:
    ligand_name = log_file.split('/')[-1].replace('.log', '')
    with open(log_file, "r") as f:
        for line in f:
            if line.startswith("DockQ ") and ("mapping AC:AC" in line or "mapping BC:BC" in line):
                parts = line.strip().split()
                dockq = float(parts[1])
                iRMSD = float(parts[3])
                LRMSD = float(parts[5])
                fnat = float(parts[7])
                # Determine which interface:
                if "mapping AC:AC" in line:
                    interface = "A–C"
                elif "mapping BC:BC" in line:
                    interface = "B–C"
                else:
                    continue
                row = {
                    "ligand": ligand_name,
                    "interface": interface,
                    "DockQ": dockq,
                    "iRMSD": iRMSD,
                    "LRMSD": LRMSD,
                    "fnat": fnat
                }
                rows.append(row)

with open(SUMMARY_CSV, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["ligand", "interface", "DockQ", "iRMSD", "LRMSD", "fnat"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Summary CSV:  {SUMMARY_CSV}")


if __name__ == "__main__":
    main()