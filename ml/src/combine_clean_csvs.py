import csv
files = [
    'data/protocols/asvspoof2021_la_index_clean.csv', 
    'data/protocols/asvspoof2021_df_index_clean.csv', 
    'data/protocols/asvspoof2021_pa_index_clean.csv'
]
output_file = 'data/protocols/asvspoof2021_combined_index_clean.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as out_f:
    writer = csv.writer(out_f)
    for i, file in enumerate(files):
        with open(file, 'r', encoding='utf-8') as in_f:
            reader = csv.reader(in_f)
            if i > 0:
                next(reader) # skip header
            for row in reader:
                writer.writerow(row)

print('Combined clean CSV created successfully!')
