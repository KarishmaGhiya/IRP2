__author__ = 'gordon'
from flask import *
from archives.core import searchAll
from archives.core import archivesList
from lxml import etree
from archives.belgium import *
import os, logging, logging.handlers
import psycopg2 as psycopg2
import time
from werkzeug import generate_password_hash, check_password_hash
import datetime

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILENAME = BASE_DIR+'/LHARP.log'
app.logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME,
    maxBytes=1024 * 1024 * 100,
    backupCount=20
    )
app.logger.addHandler(handler)
app.config.update(dict(
    DATABASE=os.path.join('postgresql://postgres:karishma@localhost', 'postgres'),
    DEBUG=True,
    USERNAME='postgres',
    PASSWORD='karishma'
))



def connect_db():
    """Connects to the specific database."""
    #rv = psycopg2.connect(database="irp2_user", user="postgres", password="karishma", host="127.0.0.1", port="5432")
    rv = psycopg2.connect(app.config['DATABASE'])
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g,'psycopg2'):
        g.psycopg2 = connect_db()
    return g.psycopg2

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'psycopg2'):
        g.psycopg2.close()


@app.route('/')
def render_index_page():
    return render_template('layout.html')

@app.route('/showLogin')
def showLogin():
   return render_template('login.html')

@app.route('/toregister',methods=['POST','GET'])
def login():
 print "In Python Register!"
 db = get_db()
 # read the posted values from the UI
 _name = request.form['usernamesignup']
 _email = request.form['emailsignup']
 _password = request.form['passwordsignup']
 #validate the received values
 if _name and _email and _password:
     cur = psycopg2.extensions.cursor(db);
     #db.execute("INSERT INTO login_info values("+ _name+ "," +_password+","+ _email+");")	
     ''' cur1 = psycopg2.extensions.cursor(db);
     cur1.execute("SELECT username FROM login_users_info WHERE email_id = '"+ _email +"');")
     if cur1.fetchall > 0 :
     	flash('This Email id already a user');
	cur1.close()
	return redirect(url_for('showLogin'))
     else :'''	
     _password = generate_password_hash(_password)	
     cur.execute("INSERT INTO login_users_info(username, password, email_id, registered_on) values('"+ _name+ "', '" +_password+"', '"+ _email+"', '"+unicode(datetime.datetime.utcnow())+"');")	
     db.commit()
     '''cur1.close()'''
     cur.close()
     flash('User created successfully !')
     return redirect(url_for('showLogin'))  
 else:
     return json.dumps({'html':'<span>Enter the required fields</span>'})




@app.route('/tologin', methods=['GET', 'POST'])
def tologin():
  db = get_db()
  _uname = request.form['username']
  _password = request.form['password']
  _password = generate_password_hash(_password)
  cur = psycopg2.extensions.cursor(db);
  cur.execute("SELECT * FROM login_users_info WHERE username = '"+_uname+"' OR email_id = '"+_uname+"' AND password = '"+_password+"' LIMIT 1;")
  if cur.fetchall > 0 :
	cur.close()
	session['_uname'] = _uname
	return redirect(url_for('profile'))
	
  else :
	cur.close()
	return json.dumps({'html':'<span>Incorrect credentials. PLease try again.. </span>'})

  
  
 #  error = None
  #  if request.method == 'POST':
   #     if request.form['username'] != 'admin' or request.form['password'] != 'admin':
    #        error = 'Invalid Credentials. Please try again.'
     #   else:
      #      return redirect(url_for('login.html'))
#    return render_template('loginSuccess.html', error=error)
@app.route('/profile',methods=['GET','POST'])
def profile():
  if '_uname' not in session:
	return redirect(url_for('showLogin'))
  return render_template('afterlogin.html')

@app.route('/logout')
def signout():
  if '_uname' not in session:
    return redirect(url_for('showLogin'))
  session.pop('_uname', None)
  return render_template('afterlogout.html')

@app.route('/search', methods=['GET','POST'])
def search():
    inputs = request.form
    session["inputs"] = inputs
    results = searchAll(inputs, asyncSearch=True)
    #app.logger.debug("results: \n"+json.dumps(results))
    #app.logger.debug("archivesList: \n"+json.dumps(archivesList))
    return render_template("search.html", results=results, archivesList=archivesList, inputs=inputs)

@app.route('/searchafterlogin', methods=['GET','POST'])
def searchafterlogin():
    inputs = request.form
    session["inputs"] = inputs
    results = searchAll(inputs, asyncSearch=True)
    return render_template("searchafterlogin.html", results=results, archivesList=archivesList, inputs=inputs)

@app.route('/saveSearch',methods=['GET','POST'])
def saveSearch():
  #inputs = request.form
  inputs = session["inputs"]
  _uname = session["_uname"]
  results = searchAll(inputs, asyncSearch=True)	
  #return json.dumps(inputs["general"])
  #if _uname not in session:
  #return render_template("searchafterlogin.html")
  #else:
  db = get_db()
  cur = psycopg2.extensions.cursor(db);
  #format = "%a %b %d %H:%M:%S %Y"
  ts = datetime.datetime.utcnow()
  #print('_uname')
  cur.execute("INSERT INTO save_search(username, searched_on, search_key, search_results) values('"+ _uname+ "','"+unicode(ts) +"','"+str(inputs["general"]) +"', '"+json.dumps(results)+"');")	
  db.commit()
  cur.close()
  flash('Search saved  successfully !')
  return render_template("searchsaved.html")
  
  	

@app.route('/adsearch', methods=['GET','POST'])
def adsearch():
    if request.form.get("search") != None:
        session["inputs"] = request.form
    if "inputs" in session:
        inputs = session["inputs"]
        result = findresult(inputs)
        return render_template('adsearch.html',results=result)
    else:
        return render_template('adsearch.html')


@app.route('/advsearch', methods=['GET','POST'])
def advsearch():
    tree = etree.parse("bel.xml")
    inventory = tree.getroot()
    session.clear()
    # initial
    result = set(inventory.iter())
    title = request.form.get("title")
    if title != "":
        title_r = ftitle(inventory,title)
        result = result & title_r

    date = request.form["date"]
    if date != "":
        date_r = fdate(inventory,date)
        result = result & date_r

    type = request.form["type"]
    if type != "":
        type_r = ftype(inventory,type)
        result = result & type_r

    series = request.form["series"]
    if series != "":
        series_r = fseries(inventory,series)
        result = result & series_r

    text = request.form["text"]
    if text != "":
        text_r = ftext(inventory,text)
        result = result & text_r

    name = request.form["name"]
    if name != "":
        name_r = fname(inventory,name)
        result = result & name_r


    ls = getresult(result)
    print ls
    return render_template('adsearch.html',results=ls)

@app.route('/detail', methods=['GET','POST'])
def detail():
    result = request.args.get("detail")
    return render_template('detail.html',results = result)


if __name__ == '__main__':
    app.run("0.0.0.0")
