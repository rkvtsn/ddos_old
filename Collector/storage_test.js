var storage = require('./storage.js');


var PROTOCOL = { _1: "ICMP", _6: "TCP", _14: "Telnet", _17: "UDP" };

var NetFlowCollection = function () {
    
    var self = this;
    
    self.flows = 0;
    self.bytesCount = 0;
    self.packetsCount = 0;
    self.protocols = {
        TCP: 0,
        ICMP: 0,
        Telnet: 0,
        UDP: 0,
    };
    self.uniquePairs = {};
    
    self.add = function (flow) {
        self.bytesCount += flow.bytesCount;
        self.packetsCount += flow.packetsCount;
        
        self.protocols.TCP += flow.protocols.TCP || 0;
        self.protocols.ICMP += flow.protocols.ICMP || 0;
        self.protocols.Telnet += flow.protocols.Telnet || 0;
        self.protocols.UDP += flow.protocols.UDP || 0;
        
        for (var p in flow.uniquePairs) {
            self.uniquePairs[p] = 1;
        }
    };
    
};


var get_nfdata = function (d) {
    nfc = new NetFlowCollection();

    var msgBuffer = new Buffer(d, 'binary');
    
    var flowCount = msgBuffer.readUInt16BE(2);
    nfc.flows += flowCount;
    
    var flow;
    var offset = 0;
    
    for (var i = 0; i < flowCount; i++) {
        offset = 24 + (i * 48)
        
        if ((msgBuffer.length - offset) > 47) {
            flow = {};
            
            flow.src_addr = [];
            flow.src_addr[0] = msgBuffer.readUInt8(offset);
            flow.src_addr[1] = msgBuffer.readUInt8(offset + 1);
            flow.src_addr[2] = msgBuffer.readUInt8(offset + 2);
            flow.src_addr[3] = msgBuffer.readUInt8(offset + 3);
            flow.srcAddr = flow.src_addr.join('.');
            
            flow.dst_addr = [];
            flow.dst_addr[0] = msgBuffer.readUInt8(offset + 4);
            flow.dst_addr[1] = msgBuffer.readUInt8(offset + 5);
            flow.dst_addr[2] = msgBuffer.readUInt8(offset + 6);
            flow.dst_addr[3] = msgBuffer.readUInt8(offset + 7);
            flow.dstAddr = flow.dst_addr.join('.');
            
            flow.packetsCount = msgBuffer.readUInt32BE(offset + 16);
            flow.bytesCount = msgBuffer.readUInt32BE(offset + 20);
            
            flow.srcPort = msgBuffer.readUInt16BE(offset + 32);
            flow.dstPort = msgBuffer.readUInt16BE(offset + 34);
            
            flow.tcpFlags = msgBuffer.readUInt8(offset + 37);
            
            flow.protocols = {};
            flow.layerProtocol = msgBuffer.readUInt8(offset + 38);
            flow.protocols[PROTOCOL["_" + flow.layerProtocol]] = 1;
            
            flow.uniquePairs = {};
            flow.uniquePairs[flow.srcAddr + ":" + flow.srcPort + "_" + flow.dstAddr + ":" + flow.dstPort] = 1;
        }
        
        nfc.add(flow);
    }
    return nfc;
};




var test = function () {
    
    
    //var arr = [];
    
    //var b1 = new Buffer([1, 2, 3, 4]);
    //var b2 = new Buffer([6, 5]);
    
    //s1 = b1.toString('base64');
    //s2 = b2.toString('base64');
    
    //arr.push(s1);
    //arr.push(s2);

    //storage.store({
    //    time: new Date(),
    //    buffer: arr,
    //});

    storage.fetchAll(function (d) {
        console.log(d.rows.length);
        for (var i = 0; i < d.rows.length; i++) {
            if (d.rows[i]['data'] === undefined) {
                console.log("empty line");
                continue;
            }
            
            nfc = new NetFlowCollection();

            for (var j = 0; j < d.rows[i]['data'].length; j++) {
                d = new Buffer(d.rows[i]['data'][j], 'base64');
                nfc = get_nfdata(d);
            }
            
            console.log(nfc);
        }
    });

};

//test_store();

test();

//storage.test_bin();