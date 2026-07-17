import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import re

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

    # Only add the pH column if it's missing
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
    # Currently I am finding direct matches. I need to make it so that I can just match the condition and pH from the crystal condition to the key
    
    

    # Variables for below.
    cc_unknown_pH = '' #crystal condition
    cc_known_pH = ''
    well_known_pH = ''
    well_unknown_pH = ''
    pH = 0
    print(df['crystalcond'][500:550])
    unkown_pH_conditions = df['crystalcond']
    # Basically I am going through the crystal conditions in the dataframe and pulling out the raw condition and the well. Getting rid of other junk
    # Not working at the moment because I need to parse through more than two values and find the well and condition. This is a problem for me on Monday.
    for value in unkown_pH_conditions:
        n1, n2 = value.split() # need to refactor this because there are going to be conditions that include spaces in them, leading to more than two values in the split
        if len(n1) > 3:
            cc_unknown_pH = n1
            well_unknown_pH = n2
        else:
            cc_unknown_pH = n2
            well_unknown_pH = n1
    
    # for each key and value in the pH_map I am extracting the well number and condition and comparing these to the wells and conditions in the database where we don't know the pH
    # Then when we find a match we assign the database value that pH.
    # Perhaps also refactor to see if we can get rid of the tripple for loop.
    for entry in pH_map:
        for key, val in entry.items():
            num = 0
            key_split = key.split()
            while key.split != r"[A-Z]\d{1,2}\s":
                num += 1
            cc_known_pH = key_split[n]
            well_known_pH = key_split[n+1]
            pH = val
        if well_known_pH == well_unknown_pH and cc_known_pH == cc_unknown_pH:
            df['pH'] = pH

    df.to_sql('data_table', engine, if_exists='replace', index=False) #perhaps no the best way to do this. It overwrites the table everytime but for now I tbink it should work

        

        

    conn_pH_reference.close()
def main():
    find_pH()

if __name__ == "__main__":
    main()