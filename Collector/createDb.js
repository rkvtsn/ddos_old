var pg = require('pg');

var config = {
    user: 'postgres',
    password: '123456',
    database: 'postgres',
    new_database: 'traffic',
    host: 'localhost',
    port: 5432
};

var get_create_db = function () {
    return "CREATE DATABASE " + config.new_database +
        "  WITH OWNER = " + config.user +
        "       ENCODING = 'UTF8'\n" +
        "       TABLESPACE = pg_default\n" +
        //"       LC_COLLATE = 'en_US.UTF-8'\n" +
        //"       LC_CTYPE = 'en_US.UTF-8'\n" +
        "       CONNECTION LIMIT = -1;";
};

var get_create_table_flows = function () {
    return "CREATE TABLE IF NOT EXISTS flows (" +
        "   id   SERIAL NOT NULL, " +
        "   time TIMESTAMP NOT NULL, " +
        "   data TEXT[], " +
        "   atk_name VARCHAR(250)," + 
        "   atk_desc TEXT," + 
        "   PRIMARY KEY(id));";
};

var get_drop_db = function () {
    return "DROP DATABASE IF EXISTS " + config.new_database;
};


var createTable = function (f) {
    config.database = config.new_database;
    var client = new pg.Client(config);
    client.connect();
    var query = client.query(get_create_table_flows());
    query.on('end', function () {
        client.end();
        console.log("* Table created!");
        f();
    });
};

var create = function () {
    var client = new pg.Client(config);
    client.connect();
    var query1 = client.query(get_drop_db());
    query1.on('end', function () {
        console.log("* DB deleted!");
        var query2 = client.query(get_create_db());
        query2.on('end', function () {
            client.end();
            console.log("* DB created!");
            createTable(function () {
                console.log("[v] All done!");
            }); 
        });
    });    
};

create();