# -*- coding: utf-8 -*-

import os
import re
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, jsonify, send_from_directory
from werkzeug import secure_filename

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'note-file-backend.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)),
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

#Create New User
@app.route('/adduser', methods=['POST'])
def add_user():

    #check that email includes atleast one @ and .
    email=check_email(request.json['emailaddress'])
    userexist=checkUserExists(request.json['emailaddress'])
    passwordmacth=checkPasswords(request.json['password'],request.json['repassword'])
    #check that email is true ,passwords are not empty and paswords match
    if(userexist!=1):
        resp = jsonify(result="user already exist")
        resp.status_code = 400
        return resp
    if email!=1 or passwordmacth!=1 :
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
        cursor=db.execute('select userid from users where emailaddress=? and password=?',
                          [request.json['emailaddress'], request.json['password']])
        data=cursor.fetchone()
        print data[0]
        #create directory for user
        dir_route=os.path.dirname(os.path.realpath(__file__))
        dir_route=dir_route+"/userfiles/"+user
        print dir_route
        os.makedirs(dir_route)
        resp = jsonify(result=data[0])
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
#Check That passwords match
def checkPasswords(pass1,pass2):
    if pass1!=pass2 or not pass1 or not pass2:
        return 0
    else:
        return 1

def check_email(email):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return 0
    return 1

#Login with user and return userid
@app.route('/login', methods=['GET'])
def login():
    email=request.args['emailaddress']
    passwd=request.args['password']
    db = get_db()
    cursor=db.execute('select userid from users where emailaddress=? and password=?',( email,passwd))
    data=cursor.fetchone()
    if(data):
        result=data[0]
        print result
        resp = jsonify(result=result)
        resp.status_code = 200
    else:
        resp = jsonify({'result:':"Login failed"})
        resp.status_code = 401
    return resp

#Create new note under users id
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
        resp = jsonify(result="note "+data+" created")
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(result="check all fields")
        resp.status_code = 400
        return resp

#update existin note
@app.route('/updatenote', methods=['PUT'])
def update_note():
    if  request.json['id'] is not None or request.json['userid'] is not None or request.json['text'] is not None:
        db = get_db()
        id=request.json['id']
        userid=request.json['userid']
        text=request.json['text']
        id=request.json['id']
        db.execute("update notes set  text=? where id=? and  ownerid=?",(text,id,userid,))
        db.commit()
        db.close()
        resp = jsonify(result="note updated")
        resp.status_code = 200
        return resp
    else:
        resp = jsonify(result="check all fields")
        resp.status_code = 400
        return resp

#delete note from database
@app.route('/deletenote', methods=['DELETE'])
def deletenote():
    if  request.args['ownerid'] is not None or request.args['noteid'] is not None:
        noteid=request.args['noteid']
        ownerid=request.args['ownerid']
        db = get_db()
        db.execute("delete from notes where id =? and ownerid=?",(noteid,ownerid))
        db.commit()
        db.close()
        resp = jsonify(result="note deleted")
        resp.status_code = 200
        return resp
    else:
        resp = jsonify(result="check all fields")
        resp.status_code = 400
        return resp

#get list of notes.
@app.route('/getnotes', methods=['GET'])
def getnotes():
    userid=request.args['userid']
    print userid
    db = get_db()
    cursor=db.execute('select * from notes where ownerid=?',(userid,))
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

#get text of single note
@app.route('/getnote', methods=['GET'])
def getnote():
    noteid=request.args['id']
    print noteid
    db = get_db()
    cursor=db.execute('select * from notes where id=? ',(noteid,))
    data=cursor.fetchone()
    print data[3]
    if(data):
        resp = jsonify({'notetext':data[3]})
        resp.status_code = 200
    else:
        resp = jsonify({'result:':"Login failed"})
        resp.status_code = 401

    return resp


#upload fiels to users folder
@app.route('/filetransfersend',methods=['POST'] )
def filetransfersend():
    if request.method == 'POST':
        userid=request.args['id']
        print userid
        db = get_db()
        cursor=db.execute('select emailaddress from users where userid=? ',
                          [request.args['id'],])
        data=cursor.fetchone()
        print data[0]
        file = request.files['file']

        dir_route=os.path.dirname(os.path.realpath(__file__))
        dir_route=dir_route+"/userfiles/"+data[0]+"/"
        print dir_route+file.filename

        #get filename
        db.execute('insert into files (id,ownerid, name) values (?, ?, ?)',
                   [None, userid,file.filename])
        db.commit()

        #if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(dir_route,filename))
        print "done"
        return "file "+filename+" saved"

 #file request from client
@app.route('/filetransferget',methods=['get'])
def filetransferget():
    userid=request.args['userid']
    filename=request.args['filename']
    print userid
    print filename
    db = get_db()
    cursor=db.execute('select emailaddress from users where userid=? ',(userid,))
    userfiles=cursor.fetchone()
    dir_route=os.path.dirname(os.path.realpath(__file__))
    dir_route=dir_route+"/userfiles/"+userfiles[0]+"/"
    print dir_route
    print filename
    return send_from_directory(dir_route,
                               filename)

#delete file from folder and user database
@app.route('/filetransferdelete', methods=['DELETE'])
def deletefile():
    if request.args['ownerid'] is not None or request.args['filename'] is not None:
        print request.args['ownerid']
        print request.args['filename']

        db = get_db()
        cursor=db.execute('select emailaddress from users where userid=? ',
                          [request.args['ownerid'],])
        data=cursor.fetchone()
        #path to users folder
        dir_route=os.path.dirname(os.path.realpath(__file__))
        dir_route=dir_route+"/userfiles/"+data[0]+"/"

        cursor2=db.execute('select id from files where ownerid=? and name=?',
                          [request.args['ownerid'],request.args['filename'],])
        data2=cursor2.fetchone()

        os.remove(os.path.join(dir_route,request.args['filename']))
        db.execute("delete from files where id =? ",(data2[0],))
        db.commit()
        db.close()
        resp = jsonify(result="file "+request.args['filename'] +" deleted")
        resp.status_code = 200
        return resp
    else:
        resp = jsonify(result="cant delete file")
        resp.status_code = 400
        return resp

#get list of users files
@app.route('/getfilelist', methods=['GET'])
def getfiles():
    userid=request.args['userid']
    print userid
    if ('userid' in request.args):
        print userid
        db = get_db()
        cursor=db.execute('select * from files where ownerid=? ',(userid,))
        rows=cursor.fetchall()
        if(cursor.rowcount!=0):
            resp=jsonify(files=[dict(ix) for ix in rows])
            resp.status_code = 200
            return resp
    else:
        resp = jsonify({'result:':"no files found"})
        resp.status_code = 401
        return resp


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
if __name__ == '__main__':
    app.run()
