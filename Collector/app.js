var zmq = require("zmq"),
    socket_r = zmq.socket("pull"),
    socket_s = zmq.socket("push"),
    zlib = require("zlib"),
    gzip = zlib.createGzip();

var PORT_IN = 6346;
var PORT_OUT = 6347;
var IP = "127.0.0.1";



var data = {};

setInterval(function () {
    var value = Math.floor(Math.random() * 100); // !
    data.value = value; // !
    
    zlib.deflate(JSON.stringify(data), function (err, buffer) {
        if (!err) {
            socket_s.send(buffer);
            console.log('> asking ' + value);
        } else {
            console.log(err);
        }
    });
}, 1000);

socket_r.on('message', function (data) {
    console.log('> answer data ' + data);
});

socket_s.connect('tcp://' + IP + ':' + PORT_OUT);
socket_r.bind('tcp://' + IP + ':' + PORT_IN);

