/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/
#include "headers.p4"

const bit<16> TYPE_IPV4 = 0x800;

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    // state machine for  parser
    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
    }
}

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            6: parse_tcp;
            default: accept;
                }
            }
state parse_tcp {
    packet.extract(hdr.tcp);
    transition accept;
}
}
