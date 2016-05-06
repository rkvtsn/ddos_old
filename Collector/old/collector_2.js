//2nd level collector

var cluster = require('cluster');

var protocol = { _1: "ICMP", _6: "TCP", _14: "Telnet", _17: "UDP" }

var Set = require("collections/set");

var fs = require('fs');

var config = {
    numCPUs: require('os').cpus().length,
    NetFlowPort: 6344,
    interval: 1000
};

// grouping filter
var filter = {
    sp_dp: function (flow) {
        return flow.srcAddr + ":" + flow.srcPort + "_" + flow.dstAddr + ":" + flow.dstPort;
    },
    sp : function (flow) {
        return flow.srcAddr + ":" + flow.srcPort;
    },
    s_dp: function (flow) {
        return flow.srcAddr + "_" + flow.dstAddr + ":" + flow.dstPort;
    },
    s_d: function (flow) {
        return flow.srcAddr + "_" + flow.dstAddr;
    },
    all: function (flow) {
        return "package";
    },
};

// default filter_type
var filter_type = "all";
if (process.argv.length > 2 && filter.hasOwnProperty(process.argv[2]))
    filter_type = process.argv[2];


var Package = function () {
   
    r = {
        bytesCount: 0,
        packetsCount: 0,
        protocols: {
            TCP: 0,
            ICMP: 0,
            Telnet: 0,
            UDP: 0,
        },
    };
    
    r.uniquePairs = new Set();

    return r;
}

var sumPackages = function (r1, r2) {
    
    r1.bytesCount += r2.bytesCount;
    r1.packetsCount += r2.packetsCount;
    
    r1.protocols.TCP += r2.protocols.TCP;
    r1.protocols.ICMP += r2.protocols.ICMP;
    r1.protocols.Telnet += r2.protocols.Telnet;
    r1.protocols.UDP += r2.protocols.UDP;
    
    r1.uniquePairs = r1.uniquePairs.union(r2.uniquePairs);
    
    return r1;
};

var newPackageManager = function () {
    pm = {
        flows: 0,
        packages: { },
        add: function (id, value) {
            r = (this.packages.hasOwnProperty(id)) ? this.packages[id] : Package();
            this.packages[id] = sumPackages(r, value);
        },
    };
    return pm;
};


var report = function (pManager) {
    
    r = JSON.stringify(pManager);
    
    return r;
};



if (cluster.isMaster) {
    
    var i = 0;
    var cnt = 0;
    var minTime = 999999999999999;
    var maxTime = 0;
    
    config.startTime = new Date().getTime() + 3000;
    console.log(config);
    for (var i = 0; i < config.numCPUs; i++) {
        cluster.fork(config);
    }
    
    var packageManager = newPackageManager();
    
    
    function messageHandler(msg) {
        if (msg.cmd && msg.cmd == 'result') {
            cnt += 1;
            
            packageManager.flows += msg.result.flows;
            
            for (var key in msg.result.packages) {
                if (msg.result.packages.hasOwnProperty(key))
                    packageManager.add(key, msg.result.packages[key]);
            }
            
            minTime = Math.min(minTime, msg.tm);
            maxTime = Math.max(maxTime, msg.tm);
            
            if (cnt >= config.numCPUs) {
                console.log('--------------------------------');
                packageManager.time = msg.tm;
                packageManager.interval = maxTime - minTime;
                
                for (var key in packageManager.packages) {
                    if (packageManager.packages.hasOwnProperty(key)) {
                        packageManager.packages[key].pairsCount = packageManager.packages[key].uniquePairs.length;
                        packageManager.packages[key].uniquePairs = [];
                    }
                }
                
                console.log(report(packageManager));
                console.log('================================');
                
                fs.appendFile('logs_' + filter_type + '.txt', 
					report(packageManager) + "\n",
					function (err) {
                    if (err) throw err;
                });

                cnt = 0;
                minTime = 999999999999999;
                maxTime = 0;
                
                packageManager = newPackageManager();
				
            }
        }
    }
    
    Object.keys(cluster.workers).forEach(function (id) {
        cluster.workers[id].on('message', messageHandler);
    });
	
} else {
    var dgram = require("dgram");
    var async = require('async');
    var binary = require('buffer');
    var server = dgram.createSocket("udp4");
    
    server.on("error", function (err) {
        console.log("server error:\n" + err.stack);
        server.close();
    });
    
    var packageManager = newPackageManager();
    
    var q2 = async.queue(function (task, callback) {
        packageManager.add(filter[filter_type](task.flow), task.flow);
        callback();
    }, 2);
    
    var q1 = async.queue(function (task, callback) {
        msg = new Buffer(task.p, 'binary');
        msgBuffer = new Buffer(msg)
        
        flowCount = msgBuffer.readUInt16BE(2);
        packageManager.flows += flowCount;
        
        var flow;
        var offset;
        
        for (var i = 0; i < flowCount; i++) {
            offset = 24 + (i * 48);
            
            if ((msg.length - offset) > 47) {
                flow = {};
                
                flow.src_addr = [];
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
                
                //ICMP=1, TCP=6, Telnet=14, UDP=17
                flow.layerProtocol = msgBuffer.readUInt8(offset + 38);
                flow.protocols = {}
                flow.protocols[protocol["_" + flow.layerProtocol]] = 1;
                
                flow.uniquePairs = new Set([filter['sp_dp'](flow)]);
            }
            
            q2.push({ flow: flow, time: task.time });
        }
        callback();
    }, 60);
    
    server.on("message", function (msg, rinfo) {
        q1.push({ p: msg, time: new Date().getTime() });
    });
    
    schedule = setInterval(function () {
        if (process.env.startTime >= new Date().getTime()) {
            clearInterval(schedule);
            setInterval(function () {
                process.send({ cmd: 'result', tm: new Date().getTime(), result: packageManager });
                packageManager = newPackageManager();
            }, process.env.interval);
        }
    }, 1);
    
    server.bind(process.env.NetFlowPort);
}





