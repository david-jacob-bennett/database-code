import io
import pandas as pd
import matplotlib.pyplot as plt

# Paste your SQL output text here
def generate_ph_histogram():
    data_str = """3.1|10
    3.4|10
    3.7|32
    3.8|2
    4.1|3
    4.2|33
    4.3|65
    4.4|54
    4.5|100
    4.6|23
    4.7|6
    4.8|3
    4.9|23
    5.1|42
    5.2|1
    5.4|35
    5.5|89
    5.6|25
    5.7|98
    5.8|12
    5.9|13
    6.1|63
    6.2|14
    6.3|72
    6.4|7
    6.5|181
    6.6|29
    6.7|110
    6.8|129
    6.9|82
    7.0|283
    7.1|122
    7.2|63
    7.3|117
    7.4|154
    7.5|48
    7.6|39
    7.7|8
    7.8|21
    7.9|14
    8.0|20
    8.0|2
    8.2|25
    8.3|90
    8.4|42
    8.5|68
    8.6|76
    8.7|1
    8.9|7
    9.0|3
    9.2|17
    10.5|5"""

    # Load data into pandas, splitting by the pipe '|' delimiter
    df = pd.read_csv(io.StringIO(data_str), sep='|', header=None, names=['pH', 'frequency'])

    # Group by pH to combine any duplicate entries (like your two entries for 8.0)
    df = df.groupby('pH', as_index=False)['frequency'].sum()

    # Plot as a bar chart (histogram style)
    plt.figure(figsize=(10, 5))
    plt.bar(df['pH'], df['frequency'], width=0.08, color='steelblue', edgecolor='black', alpha=0.85)

    # Customize plot appearance
    plt.title('pH Distribution for Target Constructs (1TEL, 2TEL, 3TEL)', fontsize=12, pad=12)
    plt.xlabel('pH', fontsize=11)
    plt.ylabel('Frequency', fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()
def main():
    generate_ph_histogram()
if __name__ == "__main__":
    main()