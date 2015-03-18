

DROP DATABASE IF EXISTS session; 
CREATE DATABASE session;
DROP USER IF EXISTS session; 
CREATE USER session with password 'abcs'; 
\c session;
CREATE EXTENSION pgcrypto; 

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users 
(
    id serial, 
    username varchar(15) NOT NULL, 
    password varchar(100) NOT NULL,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS messages;
CREATE TABLE IF NOT EXISTS messages
(
    id serial,
    username varchar(15) NOT NULL default 'Anonymous',
    message varchar(140) NOT NULL,
    PRIMARY KEY (id)
);

GRANT select, insert on users, messages to session;
GRANT ALL on sequence users_id_seq, messages_id_seq to session; 

insert into users (username, password) VALUES ('raz', 'p00d13');
insert into users (username, password) VALUES ('ann','changeme');