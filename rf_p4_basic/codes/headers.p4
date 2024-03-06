/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

// ethernet header
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

// ipv4 header
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

// tcp header
header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}



// metadata used for recording the ranges
struct metadata {

    bit<16> flowID;

    bit<16> classID;
    bit<16> currentClassPort;

    // Multi-features
    bit<16> sPort;
    bit<16> dPort;


    bit<8> class_t0;
    bit<8> class_t1;
    bit<8> class_t2;
    bit<8> class_final;

    int<8> cert_t0;
    int<8> cert_t1;
    int<8> cert_t2;

    bit<128> cw_t0;
    bit<128> cw_t1;
    bit<128> cw_t2;

}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    tcp_t      tcp;
}
