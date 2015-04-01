import os
import uuid, hashlib, psycopg2, psycopg2.extras
import functools
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask.ext.socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__, static_url_path='')

app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.urandom(24).encode('hex')

socketio = SocketIO(app)

users = {}
rooms = ['general']

def connectToDB():
    connectionString = 'dbname=session user=session password=abcd host=localhost'
    try:
        return psycopg2.connect(connectionString)
    except:
        print("Can't connect to database chat")

def updateRoster():
    names = []
    print 'showing names..'
    for user in users:
        print users[user]['username']
        if len(users[user]['username'])==0:
            names.append('None')
        else:
            print (len(users[user]['username']))
            names.append(users[user]['username'])
    
    emit('roster', names, broadcast=True)
    
def refreshR():
    for room in rooms:
        emit('rooms', room, broadcast=True)




@socketio.on('message', namespace='/chat')
def new_message(message):
    print ("in message")
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    tmp = {'text':message['text'], 'room':message['room'], 'name':users[session['uuid']]['username']}
    print (tmp)
    query = """INSERT INTO messages (name1, message, room) 
    VALUES (%s, %s, %s);"""
    cur.execute(query, (users[session['uuid']]['username'], message['text'], message['room']))
    conn.commit()
    emit('message', tmp, broadcast=True, room=message['room'])
    
@socketio.on('new_room', namespace='/chat')
def on_room(room):
    print ("in room: " + room)
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    rooms.append(room)
    query = "INSERT INTO rooms (room1) VALUES ('%s');" % (room)
    print (cur.mogrify(query))
    cur.execute(query)
    conn.commit()
    print(room)
    for room in rooms:
        emit('rooms', room, broadcast=True)
    
@socketio.on('identify', namespace='/chat')
def on_identify(username):
    print ("in identify")
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    users[session['uuid']]={'username':username}
    session['username'] = username
    if (username != ""):
        query = "select * from users WHERE username = '%s';" % (username)
        cur.execute(query)
        if cur.fetchone():
            print cur.mogrify(query)
            print "User already Exists!"
            updateRoster()
        else:
            print "no user in database"
            
@socketio.on('login', namespace='/chat')
def on_login(pw, currentRoom):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT * from users WHERE username = %s and password = crypt(%s, password)"
    print (cur.mogrify(query), (session['username'], pw))
    cur.execute(query, (session['username'], pw))
    if cur.fetchone():
        print ("User in database")
        query = """SELECT room1 FROM rooms JOIN subscription ON roomid = rooms.id WHERE userid=(SELECT id FROM users WHERE username = '%s');"""
        cur.execute(query % (session['username']))
        results = cur.fetchall()
        for result in results:
            print result
            emit('showSubedRooms', result)
        updateRoster()
    emit('checkLogin')

@socketio.on('connect', namespace='/chat')
def test_connect():
    print ("in connect")
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    join_room('general') 
    session['uuid']=uuid.uuid1()
    query = ("SELECT name1, message, room FROM messages WHERE room='general';")
    cur.execute(query)
    results = cur.fetchall()
    message = {}
    room = {}
    
   

    for result in results:
        message['name'] = result['name1']
        message['text'] = result['message']
        message['room'] = result['room']
        emit('sendMessages', message)
        print(message)
    
    
    query = "SELECT room1 FROM rooms;"
    cur.execute(query)
    results = cur.fetchall()
   
    
    for result in results:
        room['room'] = result['room1']
        emit('sendRooms', room)
        print(result)
    print 'connected'

@socketio.on('changeRoom', namespace='/chat')
def onNewRoom(oldRoom, newRoom, name):
    print ("room change: " + newRoom)
    global newroom
    global oldroom
    newroom=newRoom
    oldroom=oldRoom
    
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    leave_room(oldRoom)
   
    emit('resetMessages')
   
   
   
   
    if (newRoom == 'general'):
        emit('enableMessagePosts')
        join_room('general')
        query = "SELECT name1, message, room FROM messages WHERE room='general';"
        cur.execute(query)
        message = {}
        results = cur.fetchall()
        
        
        
        
        
        
        
        for result in results:
            message['name'] = result['name1']
            message['text'] = result['message']
            message['room'] = result['room']
            emit('sendMessages', message)
          
    else:
        query = """SELECT * from subscription WHERE roomid = (SELECT id FROM rooms WHERE room1 = %s) AND userid = (SELECT id FROM users where username = %s);"""
        cur.execute(query, (newRoom, name))
        if (cur.fetchone()):
            join_room(newRoom)
            emit('enableMessagePosts')
            query = "SELECT name1, message, room FROM messages WHERE room = '%s';"
            cur.execute(query % newRoom)
            message = {}
            results = cur.fetchall()
            for result in results:
                message['name'] = result['name1']
                message['text'] = result['message']
                message['room'] = result['room']
                emit('sendMessages', message)
                print(message)
        else:
            emit('disableMessagePosts')
        


@socketio.on('register', namespace='/chat')
def on_register(pw):
    #print 'login '  + pw
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT * from users WHERE username = %s and password = crypt(%s, password)"
    print (cur.mogrify(query), (session['username'], pw))
    cur.execute(query, (session['username'], pw))
    if cur.fetchone():
        print ("User in database")
    else:
        query = query = "INSERT INTO users (username, password) VALUES (%s, crypt(%s, gen_salt('bf')));" 
        print (cur.mogrify(query), (session['username'], pw))
        cur.execute(query, (session['username'], pw))
        conn.commit()
        query = "SELECT room1 FROM rooms;"
        cur.execute(query)
        results = cur.fetchall()
        room = {}
        for result in results:
            room['room'] = result['room1']
            emit('sendRooms', room)
            print(result)
        updateRoster()
        #refreshR()
        emit('checkLogin')
    
@socketio.on('subscribe', namespace='/chat')
def on_subscription(username, currentRoom):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = """SELECT userid, roomid FROM subscription WHERE userid=(SELECT id FROM users WHERE username = %s) AND roomid=(SELECT id FROM rooms WHERE room1 = %s);"""
    cur.execute(query, (username, currentRoom))
    if cur.fetchone():
        print ("subscription already exists!")
    else:
        query = """INSERT INTO subscription (userid, roomid) VALUES ((SELECT id FROM users WHERE username = %s), (SELECT id FROM rooms WHERE room1 = %s));"""
        print(cur.mogrify(query, (username, currentRoom)))
        cur.execute(query, (username, currentRoom))
        conn.commit()
    
@socketio.on('search', namespace='/chat')
def on_search(term, name, room):
    print("searching")
    Results = {}
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    print(room)
    if room == 'general':
        query= "SELECT name1, message, room FROM messages WHERE room='general' AND message LIKE %s OR name1 LIKE %s ;"
        cur.execute(query, ("%" + term + "%", "%" + term + "%"))

        results = cur.fetchall()
    elif ((newroom != 'general')):    
        query= "SELECT name1, message, room FROM messages WHERE room= '%s' AND message LIKE '%s' OR name1 LIKE '%s' ;" % (room,"%" + term + "%", "%" + term + "%")
        cur.execute(query)

        results = cur.fetchall()

    for result in results:
        print (result)
        Results['name'] = result['name1']
        Results['text'] = result['message']
        emit('showResults', Results)

    
@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()
        
@app.route('/new_room', methods=['POST'])
def new_room():
    rooms.append(request.get_json()['name'])
    print(request.get_json()['name'])
    print 'updating rooms'
    refreshR()
    for room in rooms:
        print(room)
        emit('sendRooms', room)
    print 'back'

    return jsonify(success= "ok")

@app.route('/')
def hello_world():
    print 'in hello world'
    return app.send_static_file('index.html')

@app.route('/js/<path:path>')
def static_proxy_js(path):
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))