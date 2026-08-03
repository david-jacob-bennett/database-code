print("script started")
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import re

# can maybe implement this somewhere. I think for the most part I need to make my regex better.
def extract_pH(condition_text):
    if not condition_text:
        return None
    match = re.search(r'pH\s+([\d.]+)', str(condition_text))
    return match.group(1) if match else None

def find_pH():
    pH_map = {}
    # extracting the conditions that have a pH associated with them and then creating a map with the name as the key and just the pH as the value
    conn_pH_reference = sqlite3.connect('/home/benne77/2Trig/CrystalDex.db')
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
    conn_database = sqlite3.connect('/home/benne77/data.db')
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
    engine = create_engine('sqlite:////home/benne77/data.db')
    df = pd.read_sql("SELECT * FROM data_table", engine)
    
    '''Still non-functional. My algorithm for finding pH still only finds a small portion of the pH values. Not exactly sure of the cause of this other 
    than I may have currated the search algorithm to the final file that we use.'''

    # Variables for below.
    cc_unknown_pH = '' #cc = crystal condition
    cc_known_pH = ''
    well_known_pH = ''
    well_unknown_pH = ''
    pH = 0
    n = 0
    
    unkown_pH_conditions = df['crystalcond'].values.tolist()
    # Basically I am going through the crystal conditions in the dataframe and pulling out the raw condition and the well. Getting rid of other junk
    for line in unkown_pH_conditions:
        history = []
        line = str(line)
        if len(line) < 2: continue
        line = line.split()
        for i in range(len(line)):
            # current_item = line[i]
            # next_item = line[i+1]
            history.append(line[i])
        for value in history:
            if re.match(r"[A-Z]\d{1,2}", value):
                well_unknown_pH = value
                history.remove(value)
        cc_unknown_pH = ' '.join(history)
    # for each key and value in the pH_map I am extracting the well number and condition and comparing these to the wells and conditions in the database where we don't know the pH
    # Then when we find a match we assign the database value that pH.
        '''currently working on this section. It seems that the wells are successfully being  matched but not the conditions
        This is because of capitalization and other formatting issues. The unknowns_cc also sometimes have extra information
        which makes it so that it is not found in the known_cc. Am going to need to parse it in some way that we can remove the crap
        and just make sure that the important information is compared between the two.'''
        for key, val in pH_map.items():
            row = 0
            key_split = key.split()
            if well_unknown_pH == key_split[0]:
                cc_known_pH = ' '.join(key_split[1:])
                print(f"{cc_unknown_pH} ||||| {cc_known_pH}")
                if cc_unknown_pH in cc_known_pH:
                   df.iat[row, df.columns.get_loc('pH')] = val
            if well_unknown_pH == key_split[1]:
                cc_known_pH = ' '.join(key_split[2:])
                if cc_unknown_pH in cc_known_pH:
                   print(f"{cc_unknown_pH} ||||| {cc_known_pH}")
                   df.iat[row, df.columns.get_loc('pH')] = val
            row += 1
    df.to_sql('data_table', engine, if_exists='replace', index=False) #perhaps no the best way to do this. It overwrites the table everytime but for now I tbink it should work

    conn_pH_reference.close()

def main():
    find_pH()

if __name__ == "__main__":
    main()

