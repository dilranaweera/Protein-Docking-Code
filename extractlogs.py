import os
import re
import csv

def extract_log_data(log_file):
    """Extracts relevant data from a .log file based on predefined patterns."""
    print(f"Processing log file: {log_file}")
    patterns = {
        "Reading structure file": r"\[\+\] Reading structure file: (.+)",
        "Parsed structure file": r"\[\+\] Parsed structure file (.+)",
        "No. of intermolecular contacts": r"\[\+\] No\. of intermolecular contacts: (\d+)",
        "No. of charged-charged contacts": r"\[\+\] No\. of charged-charged contacts: (\d+)",
        "No. of charged-polar contacts": r"\[\+\] No\. of charged-polar contacts: (\d+)",
        "No. of charged-apolar contacts": r"\[\+\] No\. of charged-apolar contacts: (\d+)",
        "No. of polar-polar contacts": r"\[\+\] No\. of polar-polar contacts: (\d+)",
        "No. of apolar-polar contacts": r"\[\+\] No\. of apolar-polar contacts: (\d+)",
        "No. of apolar-apolar contacts": r"\[\+\] No\. of apolar-apolar contacts: (\d+)",
        "Percentage of apolar NIS residues": r"\[\+\] Percentage of apolar NIS residues: ([\d\.]+)",
        "Percentage of charged NIS residues": r"\[\+\] Percentage of charged NIS residues: ([\d\.]+)",
        "Predicted binding affinity": r"\[\+\+] Predicted binding affinity \(kcal.mol-1\):\s+([-\d\.]+)",
        "Predicted dissociation constant": r"\[\+\+] Predicted dissociation constant \(M\) at 25\.0˚C:\s+([-e\d\.]+)"
    }
    
    extracted_data = {key: "N/A" for key in patterns.keys()}
    
    with open(log_file, 'r', encoding='utf-8') as file:
        for line in file:
            for key, pattern in patterns.items():
                match = re.search(pattern, line)
                if match:
                    extracted_data[key] = match.group(1)
                    print(f"Extracted {key}: {match.group(1)}")
    
    return extracted_data

def process_directory(input_dir, output_csv):
    """Iterates through directories, extracts data from .log files, and writes to CSV."""
    print(f"Scanning directory: {input_dir}")
    csv_headers = ["Folder Name"] + list(extract_log_data(next(os.walk(input_dir))[2][0]).keys())
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_headers)
        
        for root, _, files in os.walk(input_dir):
            folder_name = os.path.basename(root)
            print(f"Processing folder: {folder_name}")
            for file in files:
                if file.endswith(".log"):
                    log_path = os.path.join(root, file)
                    print(f"Found log file: {log_path}")
                    extracted_data = extract_log_data(log_path)
                    writer.writerow([folder_name] + list(extracted_data.values()))
                    print(f"Written data for {file} to CSV.")

if __name__ == "__main__":
    input_directory = "/Users/dilrana/Desktop/Kuczera/af_ecm1_hecm1/cif_files/prodigy_results/"
    output_file = "extracted_logs.csv"
    process_directory(input_directory, output_file)
    print(f"Extraction complete. Output saved to {output_file}")