
import os
import uuid
from flask import Flask, session,render_template,url_for,redirect,request
from flask.ext.socketio import SocketIO, emit
import psycopg2, psycopg2.extras

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
#app.debug = True
socketio = SocketIO(app)


messages = []
users = {}

def connectToDB():
  connectionString = 'dbname=session user=session password=abcs host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")
    
    
def updateRoster():
    names = []
    print ('in update')
    for user_id in  users:
        print users[user_id]['username']
        if len(users[user_id]['username'])==0:
            names.append('Anonymous')
        else:
            names.append(users[user_id]['username'])
    global supernames
    supernames=names
    print supernames
    print 'broadcasting names'
    emit('roster', names, broadcast=True)
    

@socketio.on('connect', namespace='/chat')
def test_connect():
    print ("in connect")
   
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    session['uuid']=uuid.uuid1()
    query = "SELECT username,message FROM messages;"
    cur.execute(query)
    results = cur.fetchall()
    messages = {}
    for result in results:
        messages['name'] = result['username']
        messages['text'] = result['message']
        emit('message', messages)
    print (messages)
        
    #session['username']='starter name'
    print 'connected'
    
@socketio.on('search', namespace='/chat')
def search(term):
    print("searching")
    Results = {}
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT username, message from messages WHERE message LIKE %s OR username LIKE %s;"
    print(cur.mogrify(query, (term, term)))
    cur.execute(query, ("%" + term + "%", "%" + term + "%"))
    results = cur.fetchall()
    for result in results:
        print (result)
        Results['name'] = result['username']
        Results['text'] = result['message']
        emit('showResults', Results)
    

@socketio.on('message', namespace='/chat')
def new_message(message):
    print ("in message")
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #tmp = {'text':message, 'name':'testName'}
    tmp = {'text':message, 'name':users[session['uuid']]['username']}
    print (tmp)
    username1=tmp['name']
    
    query = "select * from users WHERE username = '%s';" % (username1)
    cur.execute(query)
    if cur.fetchone():
        print cur.mogrify(query)
        print "got the user wweee!"
        query = "INSERT INTO messages (username, message) VALUES ('%s', '%s');" % (tmp['name'], message)
        print (cur.mogrify(query))
        cur.execute(query)
        conn.commit()
        #updateRoster()
    else:
        print "nothngaag "
    
    #messages.append(tmp)
    emit('message', tmp, broadcast=True)
    
@socketio.on('identify', namespace='/chat')
def on_identify(username):
    print ("in identify")
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #print 'identify ' + username
    users[session['uuid']]={'username':username}
    #session['username'] = {'username':username}
    session['username'] = username
    if (username != ""):
        query = "select * from users WHERE username = '%s';" % (username)
        cur.execute(query)
        if cur.fetchone():
            print cur.mogrify(query)
            print "User already Exists!"
            #updateRoster()
        else:
            
            print "no user in database"
    
    
#@app.route('/create', methods=['GET', 'POST'])
@socketio.on('create', namespace='/chat')
def on_create(username,password):
  
    
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # if user typed in a post ..
    a=username
    b=password
    print(a,b)
      
    query ="INSERT INTO users (username, password) VALUES ('%s',%s)" % (a,"crypt( '%s',gen_salt('bf'))") % (b)
        
    print query
    cur.execute(query)
    conn.commit()
    emit('checkCreate')
    
    
@socketio.on('login', namespace='/chat')
def on_login(pw):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT * from users WHERE username = %s and password = %s"
    print (cur.mogrify(query), (session['username'], pw))
    cur.execute(query, (session['username'], pw))
    #if query returns results (username/password worked)
    if cur.fetchone():
        #session['username'] = username
        print ("User in database")
        #emit('checkLogin', True)
        updateRoster()
    else:
        emit('disconnect')
        print ("Invalid Password!") #username worked, but password was wrong
    emit('checkLogin')
    
    #users[session['uuid']]={'username':message}
    #updateRoster()


    
@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()

@app.route('/')
def hello_world():
    print 'in hello world'
    #return app.send_static_file('index.html')
    
    return render_template('index.html')
    

@app.route('/js/<path:path>')
def static_proxy_js(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    print "A"

    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
     