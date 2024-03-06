import argparse
import csv
from scapy.all import Ether, IP, TCP, sendp, get_if_list, get_if_hwaddr
import time
import os

def get_if():
    ifs = get_if_list()
    iface = None
    for i in get_if_list():
        if "s1-eth1" in i: # make it 'eth0' if running from mininet
            iface = i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def read_csv_data(csv_file):
    data = []
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

def write_packet_info_to_file(packets, batch_number):
    output_file = 'sending_flows_data.txt'  # Use a single file for all batches
    with open(output_file, 'a') as packet_info_file:  # Open the file in append mode
        # Clear the file before writing data for each batch

        packet_info_file.truncate(0)

        for packet in packets:
            sport = packet[TCP].sport
            dsport = packet[TCP].dport
            label = packet[TCP].flags
            if label == 'E':
                label = 2
            if label == 'EC':
                label = 3

            lst = [sport, dsport, label]
            line = ', '.join(map(str, lst))
            packet_info_file.write(line + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file', help='CSV file containing data for network traffic')
    args = parser.parse_args()

    data = read_csv_data(args.csv_file)
    iface = get_if()

    # Clear the output file for flow count
    output_file1 = 'sending_flow_count.txt'
    if os.path.exists(output_file1):
        os.remove(output_file1)

    # Clear the output file for flow count
    output_file2 = 'sending_flow_data.txt'
    if os.path.exists(output_file2):
        os.remove(output_file2)


    # Create a list to store packets
    packets = []

    # Initialize sent packet count to 0
    sent_packet_count = 0

    batch_size = 1000  # Number of packets to send in each batch
    batch_number = 0  # Batch number counter

    for row in data:
        sport = int(row['sport'])
        dsport = int(row['dsport'])
        label = int(row['Label'])
        packet_size = 5

        # Use the values from the CSV file to generate network packets
        addr = "10.0.2.2"  # Replace with the actual destination IP
        payload = b'\x00' * packet_size  # Create a payload of the specified size

        if label == 2: # Normal Traffic
            ec = "E"
        if label == 3: # Attacking Traffic
            ec = "EC"

        # Create a packet and add it to the list
        pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff') / \
              IP(dst=addr) / \
              TCP(sport=sport, dport=dsport, flags=ec) / \
              payload

        packets.append(pkt)

        # If the batch size is reached, send the batch, reset the list, and write packet info to a file
        if len(packets) == batch_size:
            batch_number += 1
            sendp(packets, iface=iface, verbose=False)
            sent_packet_count += batch_size  # Increment the sent packet count
            print("Sent", sent_packet_count, "flows")
            with open('sending_flow_count.txt', 'w') as flow_count_file:
                flow_count_file.write(str(sent_packet_count))

            write_packet_info_to_file(packets, batch_number)  # Write packet info to a file

            packets = []

    # Send any remaining packets
    if packets:
        batch_number += 1
        sendp(packets, iface=iface, verbose=False)
        sent_packet_count += len(packets)
        print("Sent", sent_packet_count, "packets")
        with open('sending_flow_count.txt', 'w') as flow_count_file:
            flow_count_file.write(str(sent_packet_count))

        write_packet_info_to_file(packets, batch_number)  # Write packet info to a file

if __name__ == '__main__':
    main()
