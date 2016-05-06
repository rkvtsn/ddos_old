var pg = require('pg');

var config = {
    user: 'postgres',
    password: '123456',
    database: 'traffic',
    host: 'localhost',
    port: 5432
};


exports.add = function (d) {
    
    var client = new pg.Client(config);
    client.connect(function (err) {
        if (err) {
            return console.error('could not connect to postgres', err);
        }
        client.query('INSERT INTO flows (time, data, atk_name, atk_desc) VALUES ($1, $2, $3, $4)', [d.time, d.buffer, d.atk_name, d.atk_desc], function (err, result) {
            if (err) {
                return console.error('error running query', err);
            }
            client.end();
        });
    });
}


exports.store = function (d, c) {

    pg.connect(config, function (err, client, done) {
        
        
        
        var handleError = function (err, client) {
            if (!err) {
                return false;
            }
            
            if (client) {
                done(client);
            }
            
            return true;
        };
                
    
        if (handleError(err, client)) {
            console.log(err);
            return false;
        }

        client.query('INSERT INTO flows (time, data, atk_name, atk_desc) VALUES ($1, $2, $3, $4)', [d.time, d.buffer, d.atk_name, d.atk_desc], function (err, result) {
        
            if (handleError(err, client)) {
                console.log(err);
                return false;
            }
        
            done();

            if (c != undefined) {
                c();
            }

        });
    });

};


exports.fetchAll = function (callback, limit) {
    
    if (limit === undefined || limit === null) {
        limit = "";
    } else {
        limit = " LIMIT " + limit;
    }

    pg.connect(config, function (err, client, done) {
        
        
        var handleError = function (err, client) {
            if (!err) {
                return false;
            }
            
            if (client) {
                done(client);
            }
            
            return true;
        };
        
        if (handleError(err, client)) {
            console.log(err);
            return false;
        }
        
        client.query('SELECT data, time FROM flows' + limit, [], function (err, result) {
            
            if (handleError(err, client)) {
                console.log(err);
                return false;
            }
            if (callback !== undefined) {
                callback(result);
            }
            done();
        });
    });

};