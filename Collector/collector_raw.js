var cluster = require('cluster');
var fs = require('fs');
var zmq = require("zmq");
var socket_s = zmq.socket("push");
var dgram = require("dgram");

var storage = require('./storage.js');

var config = {
    numCPUs: require('os').cpus().length,
    NetFlowPort: 6344,
    interval: 5000,
    PORT_OUT: 6347,
    PORT_IN: 6345,
    IP: "127.0.0.1",
};

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
    self.bytesArray = [];
    
    self.add = function (flow) {
        self.bytesCount += flow.bytesCount;
        self.packetsCount += flow.packetsCount;
        
        self.protocols.TCP += flow.protocols.TCP;
        self.protocols.ICMP += flow.protocols.ICMP;
        self.protocols.Telnet += flow.protocols.Telnet;
        self.protocols.UDP += flow.protocols.UDP;
        
        for (var p in flow.uniquePairs) {
            self.uniquePairs[p] = 1;
        }

    };
    
    self.uniquePairsCount = 0;
    
    self.inline = function (time) {
        self.uniquePairsCount = Object.keys(self.uniquePairs).length;
        return time + "," + self.uniquePairsCount + "," + self.bytesCount + "," + self.packetsCount;
    }
    
};

if (cluster.isMaster) {
    
    var benign = function () {
        return { name: "benign", desc: "" };
    };

    var attack = benign();
    
    socket_s.connect('tcp://' + config.IP + ':' + config.PORT_OUT);
    
    var socket_r = dgram.createSocket("udp4");
    
    socket_r.on("message", function (msg, rinfo) {
        var s = msg.toString('utf-8');
        
        console.log(s);
        
        if (s.startsWith('atk:')) {
            var atk = JSON.parse(s.substring(4));
            
            if (Object.keys(atk).length === 0 && JSON.stringify(atk) === JSON.stringify({})) {
                attack = benign();
            } else {
                attack = atk;
            }
        } else if (s.startsWith('atk_end:')) {
            attack = benign();
        }

    });

    socket_r.bind(config.PORT_IN);
    
    var i = 0;
    var cnt = 0;
    var minTime = 999999999999999;
    var maxTime = 0;
    
    var nfc = new NetFlowCollection();
    
    config.startTime = new Date().getTime() + 3000;
    console.log(config);
    
    for (var i = 0; i < config.numCPUs; i++) {
        cluster.fork(config);
    }
    
    function messageHandler(msg) {
        if (msg.cmd && msg.cmd == 'result') {
            cnt += 1;
            
            nfc.bytesArray = nfc.bytesArray.concat(msg.result.bytesArray);
            nfc.flows += msg.result.flows;
            nfc.add(msg.result);
            
            minTime = Math.min(minTime, msg.tm);
            maxTime = Math.max(maxTime, msg.tm);

            if (cnt >= config.numCPUs) {
                
                storage.store({ time: new Date(msg.tm), buffer: nfc.bytesArray, atk_name: attack['name'], atk_desc: attack['desc'] }, function () {
                    socket_s.send(nfc.inline(msg.tm));
                });
                
                console.log('Stored: ' + nfc.bytesArray.length);

                var interval = config.interval / 1000;
                var avg_speed = (nfc.bytesCount * 8 / (interval * 1024 * 1024));
                                
                console.log(nfc.inline(msg.tm));
                console.log('--------------------------------');
                console.log(avg_speed.toFixed(2) + ' mb/s');
                console.log(maxTime - minTime);
                console.log('================================');
                cnt = 0;
                minTime = 999999999999999;
                maxTime = 0;
                
                nfc = new NetFlowCollection();
            }
        }
    }
    
    Object.keys(cluster.workers).forEach(function (id) {
        cluster.workers[id].on('message', messageHandler);
    });
	
} else {
    
    var async = require('async')
    var server = dgram.createSocket("udp4");
    
    server.on("error", function (err) {
        console.log("server error:\n" + err.stack);
        server.close();
    });
    
    var nfc = new NetFlowCollection();
    
    var q2 = async.queue(function (task, callback) {
        nfc.add(task.flow);
        callback();
    }, 2);
    
    var q1 = async.queue(function (task, callback) {
        msg = new Buffer(task.pkg, 'binary');
        
        msgBuffer = new Buffer(msg);
        
        nfc.bytesArray.push(msgBuffer.toString('base64'));
        
        flowCount = msgBuffer.readUInt16BE(2);
        nfc.flows += flowCount;
        
        
        var offset;
        var flow;
        for (var i = 0; i < flowCount; i++) {
            
            offset = 24 + (i * 48)
            
            if ((msg.length - offset) > 47) {
                
                flow = {};
                
                flow.src_addr = []
                flow.src_addr[0] = msgBuffer.readUInt8(offset);
                flow.src_addr[1] = msgBuffer.readUInt8(offset + 1);
                flow.src_addr[2] = msgBuffer.readUInt8(offset + 2);
                flow.src_addr[3] = msgBuffer.readUInt8(offset + 3);
                flow.srcAddr = flow.src_addr.join('.');
                
                flow.dst_addr = []
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
                
                flow.protocols = { }
                flow.layerProtocol = msgBuffer.readUInt8(offset + 38);
                
                flow.protocols[PROTOCOL["_" + flow.layerProtocol]] = 1;
                
                flow.uniquePairs = {};
                flow.uniquePairs[flow.srcAddr + ":" + flow.srcPort + "_" + flow.dstAddr + ":" + flow.dstPort] = 1;
            }
            
            q2.push({ flow: flow, time: task.time });
        }
        callback();
    }, 60);
    
    server.on("message", function (msg, rinfo) {
        q1.push({ pkg: msg, time: new Date().getTime() });
    });
    
    schedule = setInterval(function () {
        if (process.env.startTime >= new Date().getTime()) {
            clearInterval(schedule);
            setInterval(function () {
                process.send({ cmd: 'result', tm: new Date().getTime(), result: nfc });
                nfc = new NetFlowCollection();
            }, process.env.interval);
        }
    }, 1);
    
    server.bind(process.env.NetFlowPort);
}
