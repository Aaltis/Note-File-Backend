# -*- coding: utf-8 -*-
"""
    Flaskr
    ~~~~~~

    A microblog example application written as Flask tutorial with
    Flask and sqlite3.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, jsonify
from werkzeug import secure_filename
from functools import wraps
import json

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    UPLOAD_FOLDER = '/home/aaltis/Note-File/note-file-backend',
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','zip',])
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    resp = jsonify(entries)
    resp.status_code = 200
    return resp

@app.route('/add', methods=['POST'])
def add_entry():
    db = get_db()
    data = request.get_json()
    db.execute('insert into entries (title, text,userid) values (?, ?, ?)',
              [request.json['title'], request.json['text'],request.json['userid']])
    db.commit()
    resp = jsonify(data)
    resp.status_code = 200
    return resp

@app.route('/adduser', methods=['POST'])
def add_user():

    #check that email includes atleast one @ and .
    email=check_email(request.json['emailaddress'])
    userexist=checkUserExists(request.json['emailaddress'])
    passwordmacth=checkPasswords(request.json['password'],request.json['repassword'])
    #check that email is true ,passwords are not empty and paswords match
    if email!=1 or userexist!=1 or passwordmacth!=1 :
        resp = jsonify(result="check all fields")
        resp.status_code = 400
        return resp
    else:
        request.json['password'];
        db = get_db()
        user=request.json['emailaddress']
        db.execute('insert into users (userid,emailaddress,password) values (?, ?, ?)',
                   [None,request.json['emailaddress'], request.json['password']])
        db.commit()
        #create directory for user
        dir_route=os.path.dirname(os.path.realpath(__file__))
        dir_route=dir_route+"/userfiles/"+user
        print dir_route
        os.makedirs(dir_route)
        print dir_route
        data=request.json['emailaddress']
        resp = jsonify(result=data)
        resp.status_code = 201
        return resp

def checkUserExists(email):
    print email
    db = get_db()
    cursor=db.execute('select * from users where emailaddress=?',(email,))
    data=cursor.fetchone()
    print data
    #if data is not null user exists,return 0
    if(data):
        return 0
    else:
        return 1

def checkPasswords(pass1,pass2):
    if pass1!=pass2 or not pass1 or not pass2:
        return 0
    else:
        return 1

def check_email(email):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return 0
    return 1

@app.route('/login', methods=['GET'])
def login():
    email=request.args['emailaddress']
    passwd=request.args['password']
    db = get_db()
    cursor=db.execute('select userid from users where emailaddress=? and password=?',( email,passwd))
    data=cursor.fetchone()
    #print data[0]
    if(data):
        resp = jsonify({'userid':data[0]})
        resp.status_code = 200
    else:
        resp = jsonify({'result:':"Login failed"})
        resp.status_code = 401
    db.commit()
    return resp
    #'Hello ' + request.args['emailaddress']+request.args['password']



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/createnote', methods=['POST'])
def create_note():
    #Check that request files are not empty;
    if  request.json['userid'] is not None or request.json['title'] is not None or request.json['textbody'] is not None :

        db = get_db()
        db.execute('insert into notes (id,ownerid,title,text) values (?,?, ?, ?)',
                  [None,request.json['userid'],request.json['title'], request.json['textbody']])
        db.commit()
        #create directory for user

        data=request.json['title']
        resp = jsonify(result=data)
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(result="check all fields")
        resp.status_code = 400
        return resp

@app.route('/updatenote', methods=['POST'])
def update_note():
    db = get_db()
    title=request.json['title']
    print title;
    text=request.json['textbody']
    ownerid=request.json['ownerid']
    id=[request.json['id']]
    print request.json['title']
    db.execute("update notes set title=?, text=?, ownerid=? where id=?",(title,text,ownerid,id))
    db.commit()
    #create directory for user
    data=request.json['title']
    resp = jsonify(result=data)
    resp.status_code = 200
    return resp

@app.route('/getnotes', methods=['GET'])
def getnotes():
    userid=request.args['userid']
    print userid
    db = get_db()
    cursor=db.execute('select * from notes where ownerid=? ',(userid))
    rows=cursor.fetchall()
    #print data[0]
    print cursor.rowcount
    if(cursor.rowcount!=0):
        resp=jsonify(notes=[dict(ix) for ix in rows])
        resp.status_code = 200

        return resp
    else:
        resp = jsonify({'result:':"Login failed"})
        resp.status_code = 401
        return resp
    #'Hello ' + request.args['emailaddress']+request.args['password']

@app.route('/getnote', methods=['GET'])
def getnote():
    noteid=request.args['noteid']
    print userid
    db = get_db()
    cursor=db.execute('select * from notes where id=? ',(noteid))
    data=cursor.fetchone()
    #print data[0]
    if(data):
        resp = jsonify({'notetext':data[0]})
        resp.status_code = 200
    else:
        resp = jsonify({'error:':"not found"})
        resp.status_code = 404
    db.commit()
    return resp
    #'Hello ' + request.args['emailaddress']+request.args['password']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/filetransfersend',methods=['POST'] )
def filetransfersend():
    print("we got file")
    if request.method == 'POST':
        file = request.files['file']
        #if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user = request.args.get("emailaddress")
        return user
       # response = HttpResponse("Here's the text of the Web page.")
       # response = HttpResponse("Text only, please.", content_type="text/plain")




def check_auth(username, password):
    return username == 'admin' and password == 'secret'



def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth: 
            return authenticate()

        elif not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated

@app.route('/secrets')
@requires_auth
def api_hello():
    return jsonify({'result':"Shhh this is top secret spy stuff!"})

if __name__ == '__main__':
    app.run()
