import csv
from collections import defaultdict

def read_data(file_name):
    with open(file_name, mode='r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        data = list(reader)
    return headers, data

def calculate_averages(data):
    averages = defaultdict(lambda: defaultdict(list))
    for row in data:
        gpu_id = int(float(row[1]))  # GPU ID is the second column
        for i, value in enumerate(row[2:], 2):  # Skip timestamp and GPU ID
            try:
                averages[gpu_id][i].append(float(value))
            except ValueError:
                pass  # Ignore non-numeric values
    return averages

def write_averages_to_csv(averages, headers, file_name):
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['GPU ID'] + headers[2:])  # Add GPU ID and skip timestamp
        for gpu_id, metrics in averages.items():
            avg_row = [sum(values)/len(values) for values in metrics.values()]
            writer.writerow([gpu_id] + avg_row)

# File names
input_file = 'system_monitoring_data.csv'
output_file = 'gpu_averages.csv'

# Process the data
headers, data = read_data(input_file)
averages = calculate_averages(data)
write_averages_to_csv(averages, headers, output_file)

print(f"Averages calculated and saved to {output_file}")
