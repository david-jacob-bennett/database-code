import pandas as pd
import sqlite3
import uuid
import sys
from sys import argv
import re
n = 1
def clean_header(file):
    # makes columns lowercase with no spaces. Strives to reduce columns not being recognized.
    return str(file).strip().lower().replace(' ', '_')


def rescaled(df):
    # Adds column that keeps track of if the column is a rescaled run rather than a new crystal.
    cond1 = df['diffraction_results'].str.contains(r"^[R]?[r]?escale[a-zA-Z0-9 ]*$").fillna(False)
    cond2 = df['comment'].astype(str).str.contains(r"^[R]?[r]?escale[a-zA-Z0-9 ]*$").fillna(False)
    df['rescaled'] = (cond1 | cond2)
    df['rescaled'] = df['rescaled'].astype(str)
    df['rescaled'] = df['rescaled'].replace({'1': 'True', '0': 'False'})
        
                

def load_data(out_file, run_name, excel_file_path):
    global n
    df = pd.read_excel(excel_file_path)

    # Can adjust this to whichever rows are necessary for analysis. Must keep "diffraction results" and "comment" so that the "rescaled" method works.
    master_cols = ['Directory', 'Row', 'Port', 'ContainerID', 'CrystalID', 'Protein', 'Comment', 'Status', 'Frac indexed', 'Max mosaicity', 'final Isa', 'Diffraction results', 'Spot shape',
                     'bad frames', 'Space group', 'unit cell', 'Aniso elipsoid a', 'Aniso elipsoid b', 'Aniso elipsoid c', 'Aniso Resolution', 'Iso Resolution',
                     'iso num uniq reflections', 'Num unique reflections','iso completeness %', 'Overall Completeness %', 'aniso completeness', 'aniso completeness (spherical)', 'iso redundancy', 'Redundancy', 'Rmeas',
                     'minimum CC1/2', 'iso min CC1/2', 'Minimum I/s', 'FreezingCond', 'CrystalCond', 'Metal', 'Priority', 'CrystalURL', "Twin fraction",
                     "Relative height of largest off origin patterson peak", 'pin size', 'Crystal minor axis (um)', 'Crystal major axis (um)', 'fit to dens', 
                     'norm to symmetry', 'searched for', 'LLG', 'TFZ', 'distance to origin', 'height relative to origin','unit-cell solvent content', 
                     'anisotropic']

    col_map = {c.lower(): c for c in df.columns}
    
    # Rebuild the dataframe using your master_cols, pulling data from the file if it exists
    new_df = pd.DataFrame()
    for col in master_cols:
        if col.lower() in col_map:
            # Use the existing column (preserving its actual case)
            new_df[col] = df[col_map[col.lower()]]
        else:
            # Column doesn't exist in file, fill with None
            new_df[col] = None
    df = new_df
    df['identifier'] = range(n, n + len(df))
    df['run_name'] = run_name
    n += len(df)
    full_col_order = ['identifier', 'run_name'] + master_cols
    df = df[full_col_order]

    df.columns = [clean_header(col) for col in df.columns]
    
    rescaled(df)
    
    # Connecting to SQL to import python dataframe.
    conn = sqlite3.connect(out_file)

    #importing into sqlite database.
    try:
        df.to_sql('data_table', conn, if_exists='append', index=False)
    except sqlite3.OperationalError as e:
        print(f"New columns detected. Altering the table structure: {e}")
        cursor = conn.cursor()
        for col in df.columns:
            try:
                cursor.execute(f"ALTER TABLE data_table ADD COLUMN {col} TEXT")
            except:
                pass  # Column already exists
        df.to_sql('data_table', conn, if_exists='append', index=False)
    conn.close()


def run_batch(files_to_process, out_file):
    for path, name in files_to_process.items():
        try:
            load_data(out_file, name, path)
            print(f"Successfully processed: {path}")
        except Exception as e:
            print(f"Error processing {path}: {e}")


def main():
    files_to_process = {
        '2Trig/01_Cassette_SSRL88584_21Oct2020_BL9-2 (2).xlsx':1,
        '2Trig/02_Cassette_SSRL88584_1Dec2020_BL9-2 (1).xlsx': 2, 
        '2Trig/03_Cassette_SSRL88584_12Feb2021_BL9-2 (1).xlsx': 3,
        '2Trig/04_Cassette_SSRL88584_28May2021_BL9-2 (1).xlsx': 4,
        '2Trig/05_Cassette_SSRL88584_29Jun2021_BL9-2 (1).xlsx': 5,
        '2Trig/06_Cassette_SSRL00268_blue_24Oct2021_BL9-2 (1).xlsx': 6,
        '2Trig/06.1_Cassette_SSRL00154_brown_24Oct2021_BL9-2 (1).xlsx': 6.1,
        '2Trig/07_Casette_SSRL00268_blue_8Dec2021_BL9-2 (1).xlsx': 7,
        '2Trig/07.1_Cassette_SSRL00154_brown_8Dec2021_BL9-2 (1).xlsx': 7.1,
        '2Trig/08_Casette_SSRL00268_blue_20Jan2022_BL9-2 (1).xlsx': 8,
        '2Trig/09_casette_SSRL00268_blue_21Mar2022_BL12-2 (1).xlsx': 9,
        '2Trig/10_casette_SSRL00268_blue_24Jun2022_BL12-2 (1).xlsx': 10,
        '2Trig/11_cassette_SSRL00268_blue_25Aug2023_BL9-2 (1).xlsx': 11,
        '2Trig/11.1_cassette_SSRL00154_brown_25Aug2023_BL9-2 (1).xlsx': 11.1,
        '2Trig/12_cassette_SSRL00268_blue_11Nov2023_BL9-2 (1).xlsx': 12,
        '2Trig/12.1_cassette_SSRL00154_brown_11Nov2023_BL9-2 (1).xlsx': 12.1,
        '2Trig/13_cassette_SSRL00268_blue_6Dec2023_BL9-2_BL12-2 (1).xlsx': 13,
        '2Trig/13.1_cassette_SSRL00154_brown_6Dec2023_BL9-2_BL12-2 (1).xlsx': 13.1,
        '2Trig/14_cassette_SSRL00268_blue_5Apr2024_BL12-2 (1).xlsx': 14,
        '2Trig/14.1_cassette_SSRL00154_brown_5Apr2024_BL12-2 (1).xlsx': 14.1,
        '2Trig/15_cassette_SSRL00268_blue_11Jun2024_BL12-2 (1).xlsx': 15,
        '2Trig/15.1_cassette_SSRL00154_brown_11Jun2024_BL12-2 (1).xlsx': 15.1,
        '2Trig/16_cassette_SSRL00268_Blue_6Nov2024_BL12-2 (1).xlsx': 16,
        '2Trig/16.1_cassette_SSRL00154_Brown_6Nov2024_BL12-2 (1).xlsx': 16.1,
        '2Trig/17_cassette_SSRL00268_Blue_4April2025_BL12-2.xls (1).xlsx': 17,
        '2Trig/17.1_cassette_SSRL00154_Brown_4April2025_BL12-2.xls (1).xlsx': 17.1,
        '2Trig/18_cassette_SSRL00268_blue_19Jun2025_12-2 (2).xlsx': 18,
        '2Trig/18.1_cassette_SSRL00154_brown_19Jun2025_12-2 (1).xlsx': 18.1,
        '2Trig/19_cassette_SSRL00268_blue_17Jul2025_12-2 (1).xlsx': 19,
        '2Trig/20_Cassette_SSRL00268_Blue_20Sep2025_12-2 (1).xlsx': 20,
        '2Trig/20.1_Cassette_SSRL00154_Brown_20Sep2025_12-2 (1).xlsx': 20.1,
        '2Trig/21_Cassette_SSRL00268_Blue_20Nov2025_12-2 (2).xlsx': 21,
        '2Trig/22_Cassette_SSRL00268_Blue_13May2026_BL12-2 (1).xlsx': 22,
        '2Trig/22.1_Cassette_SSRL00154_Brown_13May2026_BL12-2 (1).xlsx': 22.1,
        '2Trig/23_Cassette_SSRL00154_Brown_06July2026.xlsx': 23
                        }
    try:
        if len(sys.argv) == 2:
            run_batch(files_to_process, argv[1])
        elif len(sys.argv) == 4:
            load_data(argv[1], argv[2], argv[3])
    except TypeError as e:
        print("Incorrect amount of arguments were given. Must provide one or three arguments.")
if __name__ == "__main__":
    main()

"""Questions for Dr. Moody:
Maxmosaicity used vs Max mosaicity estimate.
num unique reflections vs reflections, cassette 11
Iso completeness vs iso overall completeness, cassette 11, 12.1
Iso redundancy vs iso overall redundancy, 13
aniso completeness vs aniso completeness (spherical), 14
"""