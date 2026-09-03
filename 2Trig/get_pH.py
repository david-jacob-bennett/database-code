print("script started")
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import re

def get_matching_pH(raw_screen_string, pH_map):
    if not raw_screen_string:
        return None
        
    cleaned = raw_screen_string.lower().strip()
    
    # 1. Normalize screen name variants (handle hyphens and common abbreviations)
    cleaned = cleaned.replace("salt-rx", "salt rx").replace("peg-ion", "peg ion")
    cleaned = cleaned.replace("btmf", "bis-tris") # Adjust if your map calls it something else
    
    # 2. Extract the well coordinate (e.g., A1, E9, H12) near the beginning/middle
    # This regex looks for a letter A-H (or A-L) followed by 1-2 digits, ignoring anything after a dash/space/comma/underscore if it's an additive note
    well_match = re.search(r'\b([a-l]\d{1,2})\b', cleaned)
    
    if not well_match:
        return None
        
    well = well_match.group(1).upper()
    
    # 3. Identify which screen family it belongs to
    screen_prefix = None
    if "index" in cleaned:
        screen_prefix = "index"
    elif "peg ion" in cleaned:
        screen_prefix = "peg ion"
    elif "salt rx" in cleaned:
        screen_prefix = "salt rx"
    elif "wizard" in cleaned:
        screen_prefix = "wizard screen"
    elif "bis-tris" in cleaned or "btmf" in cleaned:
        screen_prefix = "bis-tris" # or whatever your map uses
    else:
        screen_prefix = "crystal screen" # Fallback
        
    # 4. Construct the standardized key and check your map
    lookup_key = f"{screen_prefix} {well}"
    
    return pH_map.get(lookup_key, None)

def build_pH_map():
    pH_map = {} # crystal condition : pH value
        #need to adjust crystal screen later because it is also sometimes referred to as 'xtal'
    conditions_key = {
        0: 'crystal screen',
        1: 'index',
        2: 'peg ion',
        3: 'salt rx',
        4: 'wizard screen'
    }
    # extracting the conditions that have a pH associated with them and then creating a map with the name as the key and just the pH as the value
    conn_pH_reference = sqlite3.connect('/home/benne77/2Trig/CrystalDex.db')
    conditions_df = pd.read_sql_query("SELECT condition, GROUP_CONCAT(crystal_screen_id, ', ') as crystal_ids " \
    "FROM conditions" \
    " GROUP BY condition"
    , conn_pH_reference) 
    
    condition_with_pH_val = [f"{condition} {crystal_ids}" for condition, crystal_ids in zip(conditions_df['condition'], conditions_df['crystal_ids'])
                                if 'pH' in condition]
    
    # grabbing the pH value from each entry for the map
    n = 0
    for condition in condition_with_pH_val:
        condition_split = condition.split()
        for value in condition_split:
            if value == 'pH':
                pH_map[condition] = condition_split[n+1]
            n += 1
        n = 0

    updated_pH_map = {}

    #simplifying the keys in the pH_map
    for key, val in pH_map.items():
        # Find the matching condition
        new_key = key  # Default to the old key if no match is found
        match_trailing_num = re.search(r'\d+$', key)
        if match_trailing_num:
            idx = int(match_trailing_num.group()) - 1
            for condition_reference, condition in conditions_key.items():
                if len(conditions_key) >= idx:
                    if condition_reference - 1 == idx:
                        well = re.findall(r"[A-Z]\d{1,2}", key, re.IGNORECASE)
                        new_key = str(f"{condition} {well[0]}")
        updated_pH_map[new_key] = val
    known_prefixes = ['index', 'peg ion', 'salt rx', 'wizard screen']
    for key, val in pH_map.items():
        if any(key.lower().startswith(prefix) for prefix in known_prefixes):
            continue
        key = key.split()
        key = 'crystal screen ' + key[0]
        updated_pH_map[key] = val
        updated_pH_map['Xtal'] = val
        # Store with the new key
    updated_pH_map['Storage buffer'] = '9.3'
        
    # Moving to original variable
    pH_map = updated_pH_map
    print(len(pH_map))
    conn_pH_reference.close()
    return pH_map

def connect_to_database():
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
    return df, engine

def match_pH():
    pH_map = build_pH_map()
    df, engine = connect_to_database()

    

    # Variables for below.
    cc_unknown_pH = '' #cc = crystal condition
    cc_known_pH = ''
    well_known_pH = ''
    well_unknown_pH = ''
    pH = 0
    n = 0
    num_found = 0
    unknown_pH_conditions = df['crystalcond'].values.tolist()
    # Basically I am going through the crystal conditions in the dataframe and pulling out the raw condition and the well. Getting rid of other junk
    row = 0
    for line in unknown_pH_conditions:
        history = []
        line = str(line)
        if len(line) < 2: continue
        original_line = line
        line = line.split()
        for i in range(len(line)):
            # current_item = line[i]
            # next_item = line[i+1]
            history.append(line[i])
        for value in history:
            if re.match(r"[A-Z]\d{1,2}", value):
                well_unknown_pH = value ###### Well that we need to match with a well in our known dictionary.
                history.remove(value)
        cc_unknown_pH = ' '.join(history) ###### The rest of the stuff in the line.
        matched_before = df.iat[row, df.columns.get_loc('pH')]

    # Matching unknowns with knowns.   
        for key, val in pH_map.items():
            key_split = key.split()
            # if the well is the first thing in the list.
            if key == 'Storage buffer' and cc_unknown_pH.lower() == 'storage buffer':
                df.iat[row, df.columns.get_loc('pH')] = val
            if len(key_split) == 2 and well_unknown_pH in key_split[1]:
                num_found = 1
                if key_split[1].lower() in cc_unknown_pH.lower():
                    num_found = 2 
                if num_found >= 2: 
                    df.iat[row, df.columns.get_loc('pH')] = val
            if len(key_split) == 3 and well_unknown_pH in key_split[2]:
                num_found = 1
                tray_type = f"{key_split[0]} {key_split[1]}"
                if tray_type.lower() in cc_unknown_pH.lower():
                    num_found = 2
                if num_found >= 2: 
                    df.iat[row, df.columns.get_loc('pH')] = val
                # Concatinate the first two parts and look for it in the unknown_cc
        current_ph_val = df.iat[row, df.columns.get_loc('pH')]
        if pd.isna(current_ph_val) or current_ph_val == matched_before:
            cleaned = original_line.lower().strip().replace("_", " ")
            well_match = re.search(r'\b([a-l]\d{1,2})\b', cleaned)
            if well_match:
                w = well_match.group(1).upper()
                if "index" in cleaned: prefix = "index"
                elif "peg ion" in cleaned or "peg-ion" in cleaned: prefix = "peg ion"
                elif "salt rx" in cleaned or "salt-rx" in cleaned: prefix = "salt rx"
                elif "wizard" in cleaned: prefix = "wizard screen"
                else: prefix = "crystal screen"
                
                fallback_key = f"{prefix} {w}"
                if fallback_key in pH_map:
                    df.iat[row, df.columns.get_loc('pH')] = pH_map[fallback_key]
        row += 1

    # Reworking that last section. Can look up the crystal condition via corresponding number.

    df.to_sql('data_table', engine, if_exists='replace', index=False) 
    engine.dispose()

def main():
    match_pH()

if __name__ == "__main__":
    main()



'''Need to work on the following:
1. Storage buffer is not matching'''