import csv
import glob
import re

SUMMARY_CSV = "DockQ_summary.csv"
LOG_DIR = "/Users/dilrana/Desktop/Kuczera/DockQ_logs"

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
                fnonnat = float(parts [9])
                F1 = float (parts[11])

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
                    "fnat": fnat,
                    "fnonnat": fnonnat,
                    "F1": F1
                }
                rows.append(row)

with open(SUMMARY_CSV, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["ligand", "interface", "DockQ", "iRMSD", "LRMSD", "fnat","fnonnat","F1"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Summary CSV:  {SUMMARY_CSV}")