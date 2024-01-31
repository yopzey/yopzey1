import subprocess
import time
import csv
from datetime import datetime

# Duration for monitoring (10 minutes in seconds)
monitoring_duration = 10 * 60

def get_gpu_data():
    # Get GPU data using nvidia-smi
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,power.draw,temperature.gpu,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"]).decode()
        gpu_data = []
        for line in output.strip().split("\n"):
            gpu_data.append([float(x.strip()) for x in line.split(',')])
        return gpu_data
    except subprocess.CalledProcessError:
        return []

def get_system_data():
    # Placeholder for system data collection logic
    # Replace with actual system monitoring code
    return [50, 55, 16, 32, 100, 50, 20, 100]  # Dummy data

def calculate_averages(data_points, num_gpus):
    # Calculating averages for each metric
    averages = []
    for i in range(num_gpus):
        avg_data = [sum(x[i][j] for x in data_points) / len(data_points) for j in range(6)]  # 6 metrics per GPU
        averages.append(avg_data)
    return averages

def save_to_csv(data, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        header = ['GPU', 'Avg Power (W)', 'Avg Temp (°C)', 'Avg GPU Util (%)', 'Avg Mem Used (MiB)', 'Avg Mem Total (MiB)']
        writer.writerow(header)
        for i, row in enumerate(data):
            writer.writerow([i] + row)

# Main monitoring function
def monitor_gpus(duration):
    start_time = time.time()
    data_points = []
    num_gpus = 0

    while time.time() - start_time < duration:
        gpu_data = get_gpu_data()
        if not num_gpus:
            num_gpus = len(gpu_data)
        system_data = get_system_data()  # Collect system data
        data_points.append([gpu_data[i] + system_data for i in range(num_gpus)])  # Combine GPU and system data
        time.sleep(5)  # Adjust the sleep time as needed

    # Calculate and save averages
    averaged_data = calculate_averages(data_points, num_gpus)
    save_to_csv(averaged_data, 'gpu_monitoring_data.csv')
    print("Monitoring completed. Data saved to 'gpu_monitoring_data.csv'.")

# Run the monitoring script for the specified duration
monitor_gpus(monitoring_duration)
