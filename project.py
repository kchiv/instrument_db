from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, InstrumentType, Instrument

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


APPLICATION_NAME = "Instrument Application"

engine = create_engine('sqlite:///instruments.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/instruments/')
def homepage():
    #Render homepage
    instrumenttype = session.query(InstrumentType).all()
    items = session.query(Instrument).order_by(Instrument.created_date.desc()).limit(5)
    if 'username' not in login_session:
        #If user not logged in then render public homepage
        return render_template('public-instrumenttype.html',
                                instrumenttype = instrumenttype,
                                items = items)
    else:
        #If user logged in then render homepage with options
        current_user_id = login_session['user_id']
        current_user = session.query(User).filter_by(id=current_user_id).one()
        return render_template('homepage.html',
                                instrumenttype = instrumenttype,
                                items = items,
                                current_user = current_user)

@app.route('/login')
def showLogin():
    #Render login template
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)

@app.route('/disconnect')
def disconnect():
    #Single function for disconnecting users
    #regardless of OAuth provider
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['provider']

        flash("You have successfully been logged out.")
        return redirect(url_for('homepage'))
    else:
        flash("You were not logged in to begin with.")
        return redirect(url_for('homepage'))

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        #Validate state token
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?'
        'grant_type=fb_exchange_token&client_id'
        '=%s&client_secret=%s&fb_exchange_token=%s') % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    #Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.4/me'
    #Strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    #Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px;
                    height: 300px;
                    border-radius: 150px;
                    -webkit-border-radius: 150px;
                    -moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have logged out"

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        #Validate state token
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #Obtain authorization code
    code = request.data

    try:
        #Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        #If there was an error in the access token info then abort
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        #Verify that the access token is used for the intended user
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        #Verify that the access token is valid for this app
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    #Store the access token in the session for later use
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    #Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px;
                    height: 300px;
                    border-radius: 150px;
                    -webkit-border-radius: 150px;
                    -moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: %s' % login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #Execute http GET request to revoke current token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is'
    print result

    if result['status'] == '200':
        #Reset the user's session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        #For some reason the token was invalid
        response = make_response(json.dumps('Failed to revoke for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/instruments/new/', methods=['GET','POST'])
def newInstrumentType():
    #Creates new instrument type
    if 'username' not in login_session:
        #If user not logged in then redirect to /login
        return redirect('/login')
    current_user_id = login_session['user_id']
    current_user = session.query(User).filter_by(id=current_user_id).one()
    have_error = False
    if request.method == 'POST':
        #If method is POST create new instrument type object
        if request.form['name'] == '':
            have_error = True

        if have_error:
            #If form field not filled out return error
            error_message = """You need to fill out
            all items in your form!"""
            return render_template('newinstrumenttype.html',
                                    error_message = error_message,
                                    current_user = current_user)
        else:
            instruments = InstrumentType(name_type = request.form['name'],
                                        user_id = login_session['user_id'])
            session.add(instruments)
            session.commit()
            flash("New Instrument Type Created!")
            return redirect(url_for('homepage'))
    else:
        #If method is GET return form template
        return render_template('newinstrumenttype.html',
                                current_user = current_user)

@app.route('/instruments/<int:instrument_type_id>/<string:instrument_type_name>/edit/', methods=['GET','POST'])
def editInstrumentType(instrument_type_id, instrument_type_name):
    #Edits instrument type
    instruments = session.query(InstrumentType).filter_by(id = instrument_type_id,
                                                        name_type = instrument_type_name).one()
    creator = getUserInfo(instruments.user_id)
    current_user_id = login_session['user_id']
    current_user = session.query(User).filter_by(id=current_user_id).one()
    if 'username' not in login_session:
        #If user not logged in then redirect to /login
        return redirect('/login')

    if creator.id == login_session['user_id'] and request.method == 'POST':
        #If logged in user created instrument type and method is POST
        #then edit instrument type
        if request.form['name'] != '':
            #If form field not empty fetch data from form
            instruments.name_type = request.form['name']
        else:
            #If form field empty flash error message
            flash("You must fill out all form fields!")
            return render_template('editinstrumenttype.html',
                                instruments = instruments,
                                instrument_type_name = instrument_type_name,
                                instrument_type_id = instrument_type_id,
                                current_user = current_user)
        session.add(instruments)
        session.commit()
        flash("Instrument type edited!")
        return redirect(url_for('homepage'))
    elif creator.id == login_session['user_id']:
        #If user created instrument type and method is GET then render template
        return render_template('editinstrumenttype.html',
                                instruments = instruments,
                                instrument_type_name = instrument_type_name,
                                instrument_type_id = instrument_type_id,
                                current_user = current_user)
    else:
        #Flash error message if user is not creator of instrument type
        flash("You can only edit instrument types that you created.")
        return redirect(url_for('homepage'))

@app.route('/instruments/<int:instrument_type_id>/delete/', methods=['GET','POST'])
def deleteInstrumentType(instrument_type_id):
    #Deletes instrument type
    instruments = session.query(InstrumentType).filter_by(id = instrument_type_id).one()
    creator = getUserInfo(instruments.user_id)
    items = session.query(Instrument).filter_by(instrumenttype_id = instrument_type_id).all()
    current_user_id = login_session['user_id']
    current_user = session.query(User).filter_by(id=current_user_id).one()
    if 'username' not in login_session:
        #If user not logged in then redirect to /login
        return redirect('/login')

    if creator.id == login_session['user_id'] and request.method == 'POST':
        #If logged in user created instrument type and method is POST
        #then delete instrument type and all instruments within it
        for i in items:
            session.delete(i)
        session.delete(instruments)
        session.commit()
        flash("Instrument type and all instruments deleted!")
        return redirect(url_for('homepage'))
    elif creator.id == login_session['user_id']:
        #If logged in user created instrument type and method is
        #GET then render template
        return render_template('deleteinstrumenttype.html',
                                instruments = instruments,
                                instrument_type_id = instrument_type_id,
                                current_user = current_user)
    else:
        #For everyone else flash error message
        flash("You can only delete instrument types that you created.")
        return redirect(url_for('homepage'))

@app.route('/instruments/<int:instrument_type_id>/<string:instrument_type_name>/')
def instrumentList(instrument_type_id, instrument_type_name):
    #Returns all instruments for specific instrument type
    instruments = session.query(InstrumentType).filter_by(id=instrument_type_id).one()
    instrumenttype = session.query(InstrumentType).all()
    creator = getUserInfo(instruments.user_id)
    items = session.query(Instrument).filter_by(instrumenttype_id=instrument_type_id).all()
    itemCount = session.query(Instrument).filter_by(instrumenttype_id=instrument_type_id).count()
    if 'username' not in login_session:
        #If user is not logged in then return public template
        return render_template('publicinstruments.html',
                                instruments = instruments,
                                instrumenttype = instrumenttype,
                                items = items,
                                creator = creator,
                                itemCount = itemCount)
    else:
        #If user logged in then return template with options
        current_user_id = login_session['user_id']
        current_user = session.query(User).filter_by(id=current_user_id).one()
        return render_template('instruments.html',
                                instruments = instruments,
                                instrumenttype = instrumenttype,
                                items = items,
                                creator = creator,
                                current_user = current_user,
                                itemCount = itemCount)

@app.route('/instruments/<int:instrument_type_id>/<string:instrument_type_name>/<int:instrument_id>/<string:instrument_name>/')
def singleInstrument(instrument_type_id, instrument_type_name, instrument_id, instrument_name):
    #Returns information for single instrument
    instruments = session.query(InstrumentType).filter_by(id=instrument_type_id).one()
    instrumenttype = session.query(InstrumentType).all()
    creator = getUserInfo(instruments.user_id)
    items = session.query(Instrument).filter_by(id=instrument_id).one()
    if 'username' not in login_session:
        #If user not signed in return public template
        return render_template('publicsingleinstrument.html',
                                items = items,
                                creator = creator,
                                instrumenttype = instrumenttype,
                                instruments = instruments)
    elif items.user_id != login_session['user_id']:
        #If user signed in but not creator of instrument then return public template
        current_user_id = login_session['user_id']
        current_user = session.query(User).filter_by(id=current_user_id).one()
        return render_template('publicsingleinstrument.html',
                                items = items,
                                creator = creator,
                                current_user = current_user,
                                instrumenttype = instrumenttype,
                                instruments = instruments)
    else:
        #If user signed in is creator of instrument then return template with options
        current_user_id = login_session['user_id']
        current_user = session.query(User).filter_by(id=current_user_id).one()
        return render_template('singleinstrument.html',
                                items = items,
                                creator = creator,
                                current_user = current_user,
                                instrumenttype = instrumenttype,
                                instruments = instruments)


@app.route('/instruments/<int:instrument_type_id>/new/', methods=['GET','POST'])
def newInstrumentItem(instrument_type_id):
    #Creates new instrument item
    have_error = False
    instruments = session.query(InstrumentType).filter_by(id=instrument_type_id).one()
    current_user_id = login_session['user_id']
    current_user = session.query(User).filter_by(id=current_user_id).one()
    if 'username' not in login_session:
        #Redirects user to login page if not signed in
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] == '':
            have_error = True
        if request.form['description'] == '':
            have_error = True

        if have_error:
            #If form fields are empty return error message
            error_message = """You need to fill out all the items
                                in your form!"""
            return render_template('newinstrumentitem.html',
                                    instruments = instruments,
                                    instrument_type_id = instrument_type_id,
                                    current_user = current_user,
                                    error_message = error_message)
        else:
            #Create new instrument object in DB
            newInstrumentItem = Instrument(name = request.form['name'],
                                description = request.form['description'],
                                instrumenttype_id = instrument_type_id,
                                user_id = login_session['user_id'])
            session.add(newInstrumentItem)
            session.commit()
            flash("New instrument item created!")
            return redirect(url_for('instrumentList',
                                    instrument_type_id = instrument_type_id,
                                    instrument_type_name = instruments.name_type))
    else:
        #Fetches form template if GET request
        return render_template('newinstrumentitem.html',
                                instruments = instruments,
                                instrument_type_id = instrument_type_id,
                                current_user = current_user)

@app.route('/instruments/<int:instrument_type_id>/edit/<int:instrument_id>/', methods=['GET','POST'])
def editInstrumentItem(instrument_type_id, instrument_id):
    #Function for editing individual instrument item
    instruments = session.query(InstrumentType).filter_by(id = instrument_type_id).one()
    findItem = session.query(Instrument).filter_by(id = instrument_id).one()
    creator = getUserInfo(findItem.user_id)
    current_user_id = login_session['user_id']
    current_user = session.query(User).filter_by(id=current_user_id).one()
    if 'username' not in login_session:
        #Redirects user to login page if not signed in
        return redirect('/login')

    if creator.id == login_session['user_id'] and request.method == 'POST':
        #Edits item if same user who created it
        if request.form['name'] != '':
            findItem.name = request.form['name']
        if request.form['description'] != '':
            findItem.description = request.form['description']
        session.add(findItem)
        session.commit()
        flash("Instrument edited!")
        return redirect(url_for('instrumentList', instrument_type_id = instrument_type_id,
                                                instrument_type_name = instruments.name_type))
    elif creator.id == login_session['user_id']:
        #Fetches correct template if it's same user who created it
        return render_template('editinstrumentitem.html',
                                instruments = instruments,
                                findItem = findItem,
                                instrument_type_id = instrument_type_id,
                                instrument_id = instrument_id,
                                current_user = current_user)
    else:
        #Redirects user if not creator of instrument item
        flash("You can only edit instruments that you created.")
        return redirect(url_for('instrumentList', instrument_type_id = instrument_type_id,
                                                instrument_type_name = instruments.name_type))


@app.route('/instruments/<int:instrument_type_id>/delete/<int:instrument_id>/', methods=['GET','POST'])
def deleteInstrumentItem(instrument_type_id, instrument_id):
    #Function for deleting individual instrument item
    instruments = session.query(InstrumentType).filter_by(id = instrument_type_id).one()
    findItem = session.query(Instrument).filter_by(id = instrument_id).one()
    creator = getUserInfo(findItem.user_id)
    current_user_id = login_session['user_id']
    current_user = session.query(User).filter_by(id=current_user_id).one()
    if 'username' not in login_session:
        #Redirects user to login page if not signed in
        return redirect('/login')

    if creator.id == login_session['user_id'] and request.method == 'POST':
        #Deletes item from DB if it's same user who created it
        session.delete(findItem)
        session.commit()
        flash("Instrument deleted!")
        return redirect(url_for('instrumentList', instrument_type_id = instrument_type_id,
                                                instrument_type_name = instruments.name_type))
    elif creator.id == login_session['user_id']:
        #Fetches correct template if it's same user who created it
        return render_template('deleteinstrumentitem.html',
                                instruments = instruments,
                                findItem = findItem,
                                instrument_type_id = instrument_type_id,
                                instrument_id = instrument_id,
                                current_user = current_user)
    else:
        #Redirects user if not creator of instrument item
        flash("You can only delete instruments that you created.")
        return redirect(url_for('instrumentList', instrument_type_id = instrument_type_id,
                                                instrument_type_name = instruments.name_type))


#Instrument APIs
@app.route('/type/<int:instrument_type_id>/JSON')
def instrumentOneTypeJSON(instrument_type_id):
    findItem = session.query(InstrumentType).filter_by(id = instrument_type_id).all()
    return jsonify(InstrumentType = [i.serialize for i in findItem])

@app.route('/type/<int:instrument_type_id>/instrument/<int:instrument_id>/JSON')
def instrumentOneJSON(instrument_type_id, instrument_id):
    findItem = session.query(Instrument).filter_by(instrumenttype_id = instrument_type_id,
                                                    id = instrument_id).one()
    return jsonify(Instrument = findItem.serialize)

@app.route('/type/JSON')
def instrumentTypesJSON():
    findInstrumentTypes = session.query(InstrumentType).all()
    return jsonify(InstrumentTypes = [r.serialize for r in findInstrumentTypes])

@app.route('/type/instrument/JSON')
def instrumentsJSON():
    findItem = session.query(Instrument).all()
    return jsonify(Instruments = [i.serialize for i in findItem])


####User helper functions####
def createUser(login_session):
    newUser = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

