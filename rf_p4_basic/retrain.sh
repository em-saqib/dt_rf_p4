#!/bin/bash

# Train model
python3 rf_training.py -i nb2015.csv

sleep 1

python3 rf_to_p4.py

sleep 1

simple_switch_CLI --thrift-port 9090 < rules.cmd
