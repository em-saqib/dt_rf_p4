#!/bin/bash

# Note that this is testing setup which train and test on same dataset

# Train model
python3 rf_training.py -i nb2015.csv
sleep 1

# Convert thre model rules for P4
python3 rf_to_p4.py
sleep 1

# Upload the rules to the switch
simple_switch_CLI --thrift-port 9090 < rules.cmd
sleep 1

# Send the traffic to test
parallel ::: "sudo python3 send.py nb2015.csv" "python3 monitoring.py"
