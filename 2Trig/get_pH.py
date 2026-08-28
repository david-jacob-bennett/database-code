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
    pH_map = {} # crystal condition : pH value
    #need to adjust crystal screen later because it is also sometimes referred to as 'xtal'
    conditions_key = {
        0: ['crystal screen'],
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

    # adjust pH map so that it just includes well, condition: pH
    # for key, val in pH_map.items():
    #     for condition_reference, condition in conditions_key.items():
    #         if condition_reference == key[-1]:
    #             key = condition
    # print(pH_map)
    updated_pH_map = {}

    #in progress. Not really currently working. 
    for key, val in pH_map.items():
        # Find the matching condition
        new_key = key  # Default to the old key if no match is found
        for condition_reference, condition in conditions_key.items():
            idx = int(str(key[-1]).strip()) - 1
            
            if len(conditions_key) >= idx:
                # print(f"{condition_reference} :::::: {conditions_key[idx]}")
                if condition_reference - 1 == idx:
                    if re.match(r"[A-Z]\d{1,2}", key):
                    #also need to compare the well and connect that. Havent figured it out yet. 
                        new_key = str(condition)
                        break  # Stop searching once a match is found
                
        # Store with the new key
        updated_pH_map[new_key] = val
        
    # If you want to replace the original variable:
    pH_map = updated_pH_map
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
    row = 0
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
                well_unknown_pH = value ###### Well that we need to match with a well in our known dictionary.
                history.remove(value)
        cc_unknown_pH = ' '.join(history) ###### The rest of the stuff in the line.
    # for each key and value in the pH_map I am extracting the well number and condition and comparing these to the wells and conditions in the database where we don't know the pH
    # Then when we find a match we assign the database value that pH.
        '''currently working on this section. It seems that the wells are successfully being  matched but not the conditions
        This is because of capitalization and other formatting issues. The unknowns_cc also sometimes have extra information
        which makes it so that it is not found in the known_cc. Am going to need to parse it in some way that we can remove the crap
        and just make sure that the important information is compared between the two.'''
    # now that we have our unknowns we switch to parsing through the pH_map 
    # Need to figure out how to get the crystal condition mapping that was done in crystaldex into my dictionary.
    # Then we can find the cc easily, find the well, and then map to a pH   
        for key, val in pH_map.items():
            key_split = key.split()

            # if the well is the first thing in the list.
            if well_unknown_pH == key_split[0]:
                num_found = 0

                # This is a good start. We are matching some conditions. Need to make sure they are matching correctly and need to figure out how to match the ones where the formatting is not good.
                
                for cc_pH_map in key_split[1:]:
                    if cc_pH_map.lower() in cc_unknown_pH.lower() or cc_unknown_pH.lower() in cc_pH_map.lower(): #Thinking that this is why about 1000 of the conditions are not matching.
                        num_found += 1
                if num_found >= 2: 
                    df.iat[row, df.columns.get_loc('pH')] = val

            # if the well is the second thing in the list rather than the first.
            if well_unknown_pH == key_split[1]:
                num_found = 0

                
                for cc_pH_map in key_split[1:]:
                    if cc_pH_map.lower() in cc_unknown_pH.lower() or cc_unknown_pH.lower() in cc_pH_map.lower(): #Thinking that this is why about 1000 of the conditions are not matching.
                        num_found += 1
                if num_found >= 2: 
                    df.iat[row, df.columns.get_loc('pH')] = val 
        
        row += 1


    # Reworking that last section. Can look up the crystal condition via corresponding number.


    # print(unkown_pH_conditions)
    df.to_sql('data_table', engine, if_exists='replace', index=False) #perhaps no the best way to do this. It overwrites the table everytime but for now I tbink it should work
    conn_pH_reference.close()

def main():
    find_pH()

if __name__ == "__main__":
    main()



'''Currently don't have any Salt Rx in the pH_map'''