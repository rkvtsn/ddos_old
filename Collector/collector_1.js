// 1st level collector

var cluster = require('cluster');

//ICMP=1, TCP=6, Telnet=14, UDP=17
var protocol = { _1: "ICMP", _6: "TCP", _14: "Telnet", _17: "UDP" }

var newResult = function () {
    
    r = {
        flows: 0,
        bytesCount: 0,
        packetsCount: 0,
        protocols: {
            TCP: 0,
            ICMP: 0,
            Telnet: 0,
            UDP: 0,
        },
        uniquePairs: {}
    };
    
    return r;
}

var sumResults = function (r1, r2) {
    r1.bytesCount += r2.bytesCount;
    r1.packetsCount += r2.packetsCount;
    
    r1.protocols.TCP += r2.protocols.TCP;
    r1.protocols.ICMP += r2.protocols.ICMP;
    r1.protocols.Telnet += r2.protocols.Telnet;
    r1.protocols.UDP += r2.protocols.UDP;
    
    for (var p in r2.uniquePairs) {
        r1.uniquePairs[p] = 1;
    }
    
    return r1;
}


var config = {
    numCPUs: require('os').cpus().length,
    NetFlowPort: 6344,
    interval: 5000
};


if (cluster.isMaster) {
    
    var i = 0;
    var cnt = 0;
    var minTime = 999999999999999;
    var maxTime = 0;
    
    var result = newResult();
    
    
    config.startTime = new Date().getTime() + 3000
    console.log(config);
    for (var i = 0; i < config.numCPUs; i++) {
        cluster.fork(config);
    }
    
    function messageHandler(msg) {
        if (msg.cmd && msg.cmd == 'result') {
            cnt += 1;
            result.flows += msg.result.flows;
            result = sumResults(result, msg.result);
            result.uniquePairsCount = Object.keys(result.uniquePairs).length;
            
            minTime = Math.min(minTime, msg.tm);
            maxTime = Math.max(maxTime, msg.tm);
            if (cnt >= config.numCPUs) {
                result.uniquePairs = {};
                console.log(result);
                console.log('--------------------------------');
                console.log(msg.tm);
                console.log('--------------------------------');
                console.log(maxTime - minTime);
                console.log('================================');
                cnt = 0;
                minTime = 999999999999999;
                maxTime = 0;
                
                result = newResult();
				
            }
        }
    }
    
    Object.keys(cluster.workers).forEach(function (id) {
        cluster.workers[id].on('message', messageHandler);
    });
	
} else {
    var binary = require('buffer');
    var dgram = require("dgram");
    var async = require('async')
    var server = dgram.createSocket("udp4");
    
    server.on("error", function (err) {
        console.log("server error:\n" + err.stack);
        server.close();
    });
    
    var result = newResult();
    
    var q2 = async.queue(function (task, callback) {
        result = sumResults(result, task.flow);
        
        //flows.push(task.flow);
        callback();
    }, 2);
    
    var q1 = async.queue(function (task, callback) {
        msg = new Buffer(task.packege, 'binary');
        msgBuffer = new Buffer(msg)
        
        flowCount = msgBuffer.readUInt16BE(2);
        result.flows += flowCount;
        
        var flow;
        var offset;
        
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
                
                // flow.nexthop = [];
                // flow.nexthop[0] = msgBuffer.readUInt8(offset + 8);
                // flow.nexthop[1] = msgBuffer.readUInt8(offset + 9);
                // flow.nexthop[2] = msgBuffer.readUInt8(offset + 10);
                // flow.nexthop[3] = msgBuffer.readUInt8(offset + 11);
                
                // flow.input = msgBuffer.readUInt16BE(offset + 12);
                // flow.output = msgBuffer.readUInt16BE(offset + 14);
                
                flow.packetsCount = msgBuffer.readUInt32BE(offset + 16);
                flow.bytesCount = msgBuffer.readUInt32BE(offset + 20);
                
                //flow.first = msgBuffer.readUInt32BE(offset + 24);
                //flow.last = msgBuffer.readUInt32BE(offset + 28);
                
                flow.srcPort = msgBuffer.readUInt16BE(offset + 32);
                flow.dstPort = msgBuffer.readUInt16BE(offset + 34);
                
                // flow.onePadByte = msgBuffer.readUInt8(offset + 36);
                
                flow.tcpFlags = msgBuffer.readUInt8(offset + 37);
                
                //ICMP=1, TCP=6, Telnet=14, UDP=17
                flow.layerProtocol = msgBuffer.readUInt8(offset + 38);
                flow.protocols = {}
                flow.protocols[protocol["_" + flow.layerProtocol]] = 1;
                
                //flow.uniquePairs = new Set([task.flow.srcAddr + ":" + task.flow.srcPort]);
                
                flow.uniquePairs = {};
                flow.uniquePairs[flow.srcAddr + ":" + flow.srcPort + "_" + flow.dstAddr + ":" + flow.dstPort] = 1;
				
				// flow.tos = msgBuffer.readUInt8(offset + 39);
                
				// flow.srcSysID = msgBuffer.readUInt16BE(offset + 40);
                // flow.dstSysID = msgBuffer.readUInt16BE(offset + 42);
                
				// flow.srcMask = msgBuffer.readUInt8(offset + 44);
                // flow.dstMask = msgBuffer.readUInt8(offset + 45);
				
            }
            
            q2.push({ flow: flow, time: task.time });
        }
        callback();
    }, 60);
    
    server.on("message", function (msg, rinfo) {
        q1.push({ packege: msg, time: new Date().getTime() });
    });
    
    schedule = setInterval(function () {
        if (process.env.startTime >= new Date().getTime()) {
            clearInterval(schedule)
            setInterval(function () {
                process.send({ cmd: 'result', tm: new Date().getTime(), result: result });
                result = newResult();
            }, process.env.interval);
        }
    }, 1);
    
    server.bind(process.env.NetFlowPort);
}
