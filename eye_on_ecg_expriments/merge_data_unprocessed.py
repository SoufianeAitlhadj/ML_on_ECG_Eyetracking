import pandas as pd
import glob
import os

def get_metadata_value(line):
    parts = line.strip().split(",")
    return parts[1].strip() if len(parts) > 1 else ""

def detect_separator(lines, header_row_index):
    """Detect whether the data is tab or comma separated."""
    header_line = lines[header_row_index].strip()
    tab_count = header_line.count("\t")
    comma_count = header_line.count(",")
    return "\t" if tab_count > comma_count else ","

def parse_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    gender = None
    group = None
    header_row_index = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#Respondent Gender"):
            gender = get_metadata_value(line)
        elif stripped.startswith("#Respondent Group"):
            group = get_metadata_value(line)
        elif stripped.startswith("#DATA"):
            header_row_index = i + 1

    if header_row_index is None:
        raise ValueError(f"Could not find '#DATA' marker in {file_path}")

    # ✅ Auto-detect delimiter by inspecting the header line
    sep = detect_separator(lines, header_row_index)

    df = pd.read_csv(file_path, skiprows=header_row_index, encoding="utf-8-sig",
                     sep=sep, low_memory=False)

    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()

    df.insert(0, "Respondent Gender", gender)
    df.insert(1, "Respondent Group", group)
    df.insert(0, "source_file", os.path.basename(file_path))

    print(f"  ✅ {os.path.basename(file_path)}: {len(df)} rows, "
          f"{len(df.columns)} columns [sep={'TAB' if sep == chr(9) else 'COMMA'}]")
    return df

def merge_participant_files(folder_path="participants_data", output_file="all_participant_merged.csv"):
    csv_files = [f for f in sorted(glob.glob(os.path.join(folder_path, "*.csv")))
                 if os.path.basename(f) != "ExportMerge.csv"]

    if not csv_files:
        print(f"No CSV files found in '{folder_path}'.")
        return

    print(f"Found {len(csv_files)} files to merge...\n")

    merged_dfs = []
    for file in csv_files:
        try:
            df = parse_file(file)
            merged_dfs.append(df)
        except Exception as e:
            print(f"  ❌ Skipped {os.path.basename(file)}: {e}")

    if not merged_dfs:
        print("No files were successfully parsed.")
        return

    print(f"\nConcatenating {len(merged_dfs)} dataframes...")
    merged_df = pd.concat(merged_dfs, ignore_index=True, join="outer")

    print(f"Saving to '{output_file}'...")
    merged_df.to_csv(output_file, index=False)

    print(f"\n✅ Done! {len(csv_files)} files → '{output_file}'")
    print(f"   {len(merged_df)} rows × {len(merged_df.columns)} columns")

if __name__ == "__main__":
    merge_participant_files(folder_path="../participants_data", output_file="all_participant_merged.csv")