import os
import zipfile
from pathlib import Path

zip_filename = "code.zip"

# Clean up any existing code.zip
if os.path.exists(zip_filename):
    os.remove(zip_filename)

files_to_add = []

# Add top-level files
for top_file in ["README.md", "requirements.txt"]:
    if os.path.exists(top_file):
        files_to_add.append((top_file, top_file))

# Add top-level evaluation reports
for eval_file in ["evaluation/evaluation_report.md", "evaluation/usage_report.md"]:
    if os.path.exists(eval_file):
        files_to_add.append((eval_file, eval_file))

# Add code directory recursively, skipping __pycache__, .pyc, .DS_Store, and scratch
for root, dirs, files in os.walk("code"):
    if "__pycache__" in root or "scratch" in root:
        continue
    for f in files:
        if f.endswith((".pyc", ".pyo", ".DS_Store")):
            continue
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, ".")
        files_to_add.append((full_path, rel_path))

# Sort file list for deterministic zip creation
files_to_add.sort(key=lambda x: x[1])

with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
    for full_path, arcname in files_to_add:
        zipf.write(full_path, arcname)

print(f"Created {zip_filename} with {len(files_to_add)} files.")

# Verify contents
with zipfile.ZipFile(zip_filename, "r") as zipf:
    names = zipf.namelist()
    print(f"Total entries in zip: {len(names)}")
    has_dataset_folder = any(n.startswith("dataset/") or n.startswith("dataset\\") for n in names)
    has_pycache = any("__pycache__" in n for n in names)
    has_scratch = any("scratch" in n for n in names)
    has_top_eval_report = "evaluation/evaluation_report.md" in names
    has_top_usage_report = "evaluation/usage_report.md" in names
    has_code_eval_report = "code/evaluation/evaluation_report.md" in names
    has_code_usage_report = "code/evaluation/usage_report.md" in names
    has_readme = "README.md" in names
    has_requirements = "requirements.txt" in names

    print(f"Has dataset folder: {has_dataset_folder} (Must be False)")
    print(f"Has __pycache__: {has_pycache} (Must be False)")
    print(f"Has scratch: {has_scratch} (Must be False)")
    print(f"Has evaluation/evaluation_report.md: {has_top_eval_report} (Must be True)")
    print(f"Has evaluation/usage_report.md: {has_top_usage_report} (Must be True)")
    print(f"Has code/evaluation/evaluation_report.md: {has_code_eval_report} (Must be True)")
    print(f"Has code/evaluation/usage_report.md: {has_code_usage_report} (Must be True)")
    print(f"Has README.md: {has_readme} (Must be True)")
    print(f"Has requirements.txt: {has_requirements} (Must be True)")

    if (
        not has_dataset_folder
        and not has_pycache
        and not has_scratch
        and has_top_eval_report
        and has_top_usage_report
        and has_code_eval_report
        and has_code_usage_report
        and has_readme
        and has_requirements
    ):
        print("[SUCCESS] code.zip is verified and ready for submission!")
    else:
        print("[ERROR] Verification failed!")
