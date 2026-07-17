import pandas as pd
import sqlite3
from sqlalchemy import create_engine

def find_pH():
    pH_map = {}

    # extracting the conditions that have a pH associated with them and then creating a map with the name as the key and just the pH as the value
    conn_pH_reference = sqlite3.connect('2Trig/CrystalDex.db')
    conditions_df = pd.read_sql_query("SELECT DISTINCT condition FROM conditions", conn_pH_reference)
    condition_with_pH_val = [item for item in conditions_df['condition'] if 'pH' in str(item)]
    
    # grabbing the pH value from each entry for the map
    n = 0
    for condition in condition_with_pH_val:
        condition_split = condition.split()
        for value in condition_split:
            if value == 'pH':
                pH_map[condition] = condition_split[n+1]
            n += 1
        n = 0
    
    # make new column in database
    conn_database = sqlite3.connect('data.db')
    cursor = conn_database.cursor()

    cursor.execute("PRAGMA table_info(data_table)")
    
    columns = [info[1] for info in cursor.fetchall()]

    # Only add the column if it's missing
    if 'pH' not in columns:
        cursor.execute("ALTER TABLE data_table ADD COLUMN pH TEXT")
        conn_database.commit()
        print("Column 'pH' added successfully.")
    else:
        print("Column 'pH' already exists, skipping.")

    conn_database.close()
    # if the condition in the database is equal to a condition in the map then make the pH column equal to the corresponding value in the map.
    engine = create_engine('sqlite:///data.db')
    df = pd.read_sql("SELECT * FROM data_table", engine)
    df['pH'] = df['crystalcond'].map(pH_map)
    df.to_sql('data_table', engine, if_exists='replace', index=False) #perhaps no the best way to do this. It overwrites the table everytime but for now I tbink it should work


    


    conn_pH_reference.close()
def main():
    find_pH()

if __name__ == "__main__":
    main()