/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {


    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(egressSpec_t port) {
            standard_metadata.egress_spec = port;
            hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        }

    /* Assign classes for model RF */
    action SetClass_t0(bit<8> classe, int<8> cert) {
        meta.class_t0 = classe;
        meta.cert_t0 = cert;

    }
    action SetClass_t1(bit<8> classe, int<8> cert) {
        meta.class_t1 = classe;
        meta.cert_t1 = cert;

    }
    action SetClass_t2(bit<8> classe, int<8> cert) {
        meta.class_t2 = classe;
        meta.cert_t2 = cert;

    }

    action set_final_class(bit<8> class_result) {
        meta.class_final = class_result;
        hdr.ipv4.ttl = meta.class_final;
        //ipv4_forward();
    }

    /* Feature table actions for RF */
    action SetCode_f0(bit<64> code0, bit<64> code1, bit<64> code2) {
        meta.cw_t0[127:64] = code0;
        meta.cw_t1[127:64] = code1;
        meta.cw_t2[127:64] = code2;
    }
    action SetCode_f1(bit<64> code0, bit<64> code1, bit<64> code2) {
        meta.cw_t0[63:0] = code0;
        meta.cw_t1[63:0] = code1;
        meta.cw_t2[63:0] = code2;
    }

table tbl_f0{
key = {
    meta.sPort : range ;
        }
        actions = {
            NoAction;
            SetCode_f0;
                }
                    size = 1024;
}

table tbl_f1{
key = {
    meta.dPort : range ;
        }
        actions = {
            NoAction;
            SetCode_f1;
                }
                    size = 1024;
}


/* Code tables for RF*/

table tbl_cw0{
key = {
    meta.cw_t0: ternary;
        }
        actions = {
            NoAction;
            SetClass_t0;
                }
                    size = 1024;
}

table tbl_cw1{
key = {
    meta.cw_t1: ternary;
        }
        actions = {
            NoAction;
            SetClass_t1;
                }
                    size = 1024;
}

table tbl_cw2{
key = {
    meta.cw_t2: ternary;
        }
        actions = {
            NoAction;
            SetClass_t2;
                }
                    size = 1024;
}


/* Determine classification result by majority vote of RF trees */
table voting_table{
key = {
      meta.class_t0: exact;
      meta.class_t1: exact;
      meta.class_t2: exact;
        }
        actions = {
            NoAction;
            set_final_class;
                }
                    size = 1024;
}

// When there is no majority from voting table
bit<1> diff_0_1;
bit<1> diff_0_2;
bit<1> diff_1_0;
bit<1> diff_1_2;
bit<1> diff_2_0;
bit<1> diff_2_1;

// Action computes difference between certainty values
action diff_x_y(){
    diff_0_1 = (meta.cert_t1 - meta.cert_t0)[7:7];
    diff_0_2 = (meta.cert_t2 - meta.cert_t0)[7:7];
    diff_1_0 = (meta.cert_t0 - meta.cert_t1)[7:7];
    diff_1_2 = (meta.cert_t2 - meta.cert_t1)[7:7];
    diff_2_0 = (meta.cert_t0 - meta.cert_t2)[7:7];
    diff_2_1 = (meta.cert_t1 - meta.cert_t2)[7:7];
}

apply {
    if (hdr.ipv4.isValid() ) {
            if(hdr.ipv4.protocol ==6) {

                // 1. Take hash of flow
                hash(meta.flowID,
                    HashAlgorithm.crc16,
                    (bit<16>)0,
                    {hdr.tcp.srcPort,
                    hdr.tcp.dstPort},
                    (bit<32>)100000);

                meta.sPort = (bit<16>)hdr.tcp.srcPort;
                meta.dPort = (bit<16>)hdr.tcp.dstPort;

                // Apply features tables
                tbl_f0.apply();
                tbl_f1.apply();

                // Apply RF/code TABLES
                tbl_cw0.apply();
                tbl_cw1.apply();
                tbl_cw2.apply();

                // Apply classification table
                // voting_table.apply();

                // Determine group
                if (voting_table.apply().hit) {

                      if (meta.class_final == 0){
                          ipv4_forward(3);
                      }
                      else{
                      drop();
                      }
                log_msg(" INFO FlowID : {} RealClass : {} PredictClass: {} sPort : {} dPort : {}", {meta.flowID, hdr.tcp.ecn, meta.class_final, meta.sPort, meta.dPort});
                }
                }
                }

} // Apply block end here
} // Ingress block end here
