import time
import threading
import subprocess
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os

# Specify the path to your log file
log_file_path = 'logs/s1.log'

# Lists to store data for the line chart
total_flow_counts = []
accuracy_rates = []
class_id_2_counts = []
class_id_3_counts = []

# Function to count occurrences of a specific string in the log file
def count_occurrences(keyword):
    grep_command = ["grep", "-c", keyword, log_file_path]
    result = subprocess.run(grep_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        return int(result.stdout.strip())
    else:
        #print(f"Error for '{keyword}': {result.stderr}")
        return None

# Function to read the sending flow count from the shared file
def read_sending_flow_count():
    try:
        with open('sending_flow_count.txt', 'r') as flow_count_file:
            flow_count_str = flow_count_file.read().strip()
            if flow_count_str:
                return int(flow_count_str)
            else:
                return 0
    except FileNotFoundError:
        return 0

def monitor_class_ids():
    while True:
        class_id_2_count = count_occurrences("RealClass : 1 PredictClass: 2")
        class_id_3_count = count_occurrences("RealClass : 3 PredictClass: 3")

        # Initialize to 0 if counts are None
        class_id_2_count = class_id_2_count if class_id_2_count is not None else 0
        class_id_3_count = class_id_3_count if class_id_3_count is not None else 0

        # Calculate and print the accuracy rate
        sending_flow_count = read_sending_flow_count()
        if sending_flow_count > 0:
            total_classified_count = class_id_2_count + class_id_3_count
            accuracy_rate = total_classified_count / sending_flow_count
            accuracy_rate = round(accuracy_rate, 2)
            if accuracy_rate > 1.0:
                accuracy_rate = 1.0
            if accuracy_rate < 0.0:
                accuracy_rate = 0.0
            print("\n ### STATISTICS ###")
            print("Sent Flows   : ", sending_flow_count, " Classified Flows : ", total_classified_count)
            print("Normal Flows : ", class_id_2_count, " Anomaly Flows    : ", class_id_3_count)
            print("Average Accuracy     : ", accuracy_rate)

            # Append the counts to their respective lists
            total_flow_counts.append(sending_flow_count)
            accuracy_rates.append(accuracy_rate)
            class_id_2_counts.append(class_id_2_count)
            class_id_3_counts.append(class_id_3_count)

            with open('current_accuracy.txt', 'w') as current_accuracy:
                current_accuracy.write(str(accuracy_rate))

        time.sleep(1)

def update_line_chart(i):
    if len(total_flow_counts) > 0:
        plt.clf()

        # Create the primary y-axis (left) for accuracy
        plt.plot(total_flow_counts, accuracy_rates, label="Accuracy", color='blue')
        plt.xlabel("Total Flow Count")
        plt.ylabel("Average Accuracy (%)")
        plt.ylim(0, 1)
        plt.legend(loc="upper left")

        # Create the secondary y-axis (right) for flow counts
        ax2 = plt.gca().twinx()
        ax2.plot(total_flow_counts, class_id_2_counts, label="Normal Flows", color='green', linestyle='--')
        ax2.plot(total_flow_counts, class_id_3_counts, label="Anomaly Flows", color='red', linestyle='--')
        ax2.set_ylabel("Per-Class Flow Count")
        ax2.legend(loc="upper right")
        ax2.set_ylim(0, 50000)  # Set the right y-axis limit

        plt.title("Accuracy Rate vs Total Flow Count")

        plt.tight_layout()

if __name__ == '__main__':
    # Clean log files
    output_file1 = 'sending_flow_count.txt'
    if os.path.exists(output_file1):
        os.remove(output_file1)
    output_file2 = 'current_accuracy.txt'
    if os.path.exists(output_file2):
        os.remove(output_file2)
    # Start the monitoring thread for ClassID 2 and ClassID 3
    class_id_monitoring_thread = threading.Thread(target=monitor_class_ids)
    class_id_monitoring_thread.daemon = True
    class_id_monitoring_thread.start()

    # Create and update the line chart
    ani = FuncAnimation(plt.gcf(), update_line_chart, interval=1000)

    # Display the line chart
    plt.show()
