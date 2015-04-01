DROP DATABASE IF EXISTS session; 
CREATE DATABASE session;
DROP USER IF EXISTS session; 
CREATE USER session with password 'abcd'; 
\c session;
CREATE EXTENSION pgcrypto; 

-----------------------------------------------------------
-----------------------------------------------------------
DROP TABLE IF EXISTS rooms;
CREATE TABLE IF NOT EXISTS rooms
(
    id serial,
    room1 varchar(50) NOT NULL default 'general',
    PRIMARY KEY (id)
);


-----------------------------------------------------------
-----------------------------------------------------------
DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users 
(
    id serial, 
    username varchar(15) NOT NULL, 
    password varchar(100) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE(username)
);

-----------------------------------------------------------
-----------------------------------------------------------
DROP TABLE IF EXISTS messages;
CREATE TABLE IF NOT EXISTS messages
(
    id serial,
    name1 varchar(15) NOT NULL references users(username),
    message varchar(140) NOT NULL,
    room varchar(50) NOT NULL default 'general',
    PRIMARY KEY (id)
);

-----------------------------------------------------------
-----------------------------------------------------------
DROP TABLE IF EXISTS subscription;
CREATE TABLE IF NOT EXISTS subscription
(
    id serial,
    roomid int NOT NULL references rooms(id),
    userid int NOT NULL references users(id),
    PRIMARY KEY (id)
);




GRANT select, insert on users, messages, subscription, rooms to session;


GRANT ALL on sequence users_id_seq, messages_id_seq, subscription_id_seq, rooms_id_seq to session;



INSERT into users (username, password) VALUES ('ann', crypt('changeme', gen_salt('bf')));
INSERT into users (username, password) VALUES ('raz', crypt('p00d13', gen_salt('bf')));

INSERT INTO rooms (room1) VALUES ('general');

INSERT INTO messages (name1, message, room) VALUES ('ann', 'test1 second user', default);
INSERT INTO messages (name1, message, room) VALUES ('ann', 'test2 second user', default);



INSERT INTO messages (name1, message, room) VALUES ('raz', 'test 1', default);
INSERT INTO messages (name1, message, room) VALUES ('raz', 'test 2', default);

