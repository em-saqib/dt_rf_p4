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

    action SetCode_f0(bit<128> code0) {
          meta.cw_t0[255:128] = code0;
      }
    action SetCode_f1(bit<128> code0) {
          meta.cw_t0[127:0] = code0;
          }

    /* Assign classes*/
    action SetClass_t0(bit<8> classe) {
        meta.class_final = classe;
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


/* Class table*/

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

                // Apply Classes Table
                if (tbl_cw0.apply().hit) {

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
