var zmq = require("zmq"),
    socket_r = zmq.socket("pull"),
    socket_s = zmq.socket("push"),
    zlib = require("zlib"),
    gzip = zlib.createGzip();


var CONFIG = {
    PORT_IN: 6346, 
    PORT_OUT: 6347,
    IP: "127.0.0.1",
};


var data = {};


var respounseMarker = true;
var predict = function (pManager) {
    if (respounseMarker) {
        zlib.deflate(JSON.stringify(pManager), function (err, buffer) {
            if (!err) {
                socket_s.send(buffer);
                respounseMarker = false;
                console.log('> asking ' + pManager.value);
            } else {
                console.log(err);
            }
        });
    }
};

setInterval(function () {
    var value = Math.floor(Math.random() * 100); // !
    data.value = value; // !
    predict(data);
    console.log("> monitoring " + value);
}, 1000);


socket_r.on('message', function (data) {
    respounseMarker = true;
    console.log('> answer data ' + data);
});

socket_s.connect('tcp://' + CONFIG.IP + ':' + CONFIG.PORT_OUT);
socket_r.bind('tcp://' + CONFIG.IP + ':' + CONFIG.PORT_IN);
