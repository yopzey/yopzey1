import subprocess
import time
import csv
from datetime import datetime

# Duration for monitoring (10 minutes in seconds)
monitoring_duration = 10 * 60
update_interval = 5  # Interval at which to collect data in seconds

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
    except subprocess.CalledProcessError as e:
        print("Error when calling nvidia-smi: ", e.output.decode())
        return []

def get_cpu_usage():
    # Get CPU utilization using mpstat
    output = subprocess.check_output(['mpstat', '1', '1']).decode()
    # Parse the output and extract the CPU usage
    lines = output.split('\n')
    for line in lines:
        if 'all' in line and not 'CPU' in line:
            return 100 - float(line.split()[-1])

def get_cpu_temperature():
    # Get CPU temperature using sensors
    try:
        output = subprocess.check_output(['sensors']).decode()
        # Parse the output and extract the CPU temperature
        for line in output.split('\n'):
            if 'Core 0' in line:
                temp = line.split()[2]
                return float(temp.strip('+').strip('°C'))
        # If 'Core 0' was not found in the output, return None or a default value
        return None
    except subprocess.CalledProcessError:
        # If the sensors command fails, return None or a default value
        return None

def get_ram_usage():
    # Get RAM usage from /proc/meminfo
    with open('/proc/meminfo', 'r') as file:
        meminfo = file.readlines()
    mem_total = mem_free = 0
    for line in meminfo:
        if 'MemTotal' in line:
            mem_total = float(line.split()[1])
        elif 'MemFree' in line:
            mem_free = float(line.split()[1])
    mem_used = mem_total - mem_free
    return mem_used, mem_total

def get_disk_io():
    # Get Disk I/O using iostat
    output = subprocess.check_output(['iostat', '-d', '1', '2']).decode()
    # Parse the output and extract the disk I/O stats
    lines = output.split('\n')
    for i, line in enumerate(lines):
        if 'Device' in line:
            # Assuming the next line contains the I/O stats for the disk
            disk_stats = lines[i+1].split()
            read, write = float(disk_stats[-3]), float(disk_stats[-2])
            return read, write

def get_network_usage():
    # Get Network usage using ifstat, assuming 1 second monitoring interval
    try:
        output = subprocess.check_output(['ifstat', '1', '1']).decode()
        # Parse the output and extract the network stats
        lines = output.strip().split('\n')
        # Use the last line of output, assuming it has the network stats
        if lines[-1]:
            network_stats = lines[-1].split()
            up, down = float(network_stats[-2]), float(network_stats[-1])
            return up, down
    except (subprocess.CalledProcessError, IndexError, ValueError):
        # If the ifstat command fails, or output is not as expected, return None
        return None, None


def save_to_csv(data, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        header = [
            'Timestamp',
            'GPU',
            'Avg Power (W)',
            'Avg GPU Temp (°C)',
            'Avg GPU Util (%)',
            'Avg Mem Used (MiB)',
            'Avg Mem Total (MiB)',
            'CPU Util (%)',
            'CPU Temp (°C)',
            'RAM Used (MiB)',
            'RAM Total (MiB)',
            'Disk Read (MB/s)',
            'Disk Write (MB/s)',
            'Net Upload (Mbps)',
            'Net Download (Mbps)'
        ]
        writer.writerow(header)
        for row in data:
            writer.writerow(row)

def monitor(duration, interval):
    try:
        start_time = time.time()
        data_points = []

        while time.time() - start_time < duration:
            current_time = time.time()
            elapsed_time = current_time - start_time
            remaining_time = duration - elapsed_time
            print(f"Monitoring... Time elapsed: {elapsed_time // 60} minutes {elapsed_time % 60} seconds", end='\r')

            # Collect all data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            gpu_data = get_gpu_data()
            cpu_usage = get_cpu_usage() or 0  # Use 0 if None is returned
            # cpu_temp = get_cpu_temperature() or 0  # Not used if no sensors found
            ram_used, ram_total = get_ram_usage() or (0, 0)  # Use (0, 0) if None is returned
            disk_read, disk_write = get_disk_io() or (0, 0)  # Use (0, 0) if None is returned
            net_up, net_down = get_network_usage() or (0, 0)  # Use (0, 0) if None is returned

            # Combine data for all GPUs
            if gpu_data:
                for gpu_stats in gpu_data:
                    # Remove 'cpu_temp' from the list below
                    data_points.append([timestamp] + gpu_stats + [cpu_usage, ram_used, ram_total, disk_read, disk_write, net_up, net_down])

            # Sleep until the next update interval
            time_to_sleep = interval - (time.time() - current_time)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)

        # Save the collected data to CSV
        save_to_csv(data_points, 'system_monitoring_data.csv')
        print("\nMonitoring completed. Data saved to 'system_monitoring_data.csv'.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the monitoring script for the specified duration
monitor(monitoring_duration, update_interval)
