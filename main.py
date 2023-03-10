import datetime
import random
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request, redirect, flash
from google.auth.transport import requests

app = Flask(__name__, static_url_path='/templates')

app.config['SECRET_KEY'] = "somesecretisagoodideatohaveprivacy" 
app.config['SESSION_TYPE'] = 'filesystem' 
app.config['SESSION_PERMANENT']= False

datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

driver_att = [('name', 'text'), ('age', 'number'), ('pole-position', 'number'), ('wins', 'number'), ('points', 'number'), ('titles', 'number'), ('fastest-laps', 'number'), ('team', 'number')]
team_att = [('name', 'text'), ('year-found', 'number'), ('pole-position', 'number'), ('wins', 'number'), ('titles', 'number'), ('finished-position', 'number')]
att_list = {'driver_att': driver_att, 'team_att': team_att}

def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity

def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key = entity_key)

    entity.update({
        'email': claims['email'],
        }) 
    datastore_client.put(entity)

@app.route('/add_driver', methods=['POST', 'GET'])
def addDriver():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if (request.method == 'POST'):
                query = datastore_client.query(kind='Drivers')
                query.add_filter('name', '=', request.form['name'])
                result = list(query.fetch())
                if result != []:
                    flash('Driver Already Exist!')
                    return redirect('/add_driver')
                entity_key = datastore_client.key('Drivers', claims['name'])
                entity = datastore.Entity(key=entity_key)
                obj = dict()
                for elems in driver_att:
                    obj[elems[0]] = request.form[elems[1]];
                entity.update(obj)    
                datastore_client.put(entity)
                flash('Driver added Successfully!')
                return redirect('/add_driver')
            return render_template('add-driver.html', 
                    user_info=user_info, error_messasge=error_message, data=att_list)
        except ValueError as exc:
            error_message = str(exc)
    flash('Please Login First')
    return redirect('/')

@app.route('/add_team', methods=['POST', 'GET'])
def addTeam():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if (request.method == 'POST'):
                query = datastore_client.query(kind='Teams')
                query.add_filter('name', '=', request.form['name'])
                result = list(query.fetch())
                if result != []:
                    flash('Team Already Exist!')
                    return redirect('/add_team')
                entity_key = datastore_client.key('Teams', request.form['name'])
                entity = datastore.Entity(key=entity_key)
                obj = dict()
                for elems in team_att:
                    obj[elems[0]] = request.form[elems[1]];
                entity.update(obj)
                datastore_client.put(entity)
                flash('Team added Succesfully!')
                return redirect('/add_team')
            return render_template('add-team.html', 
                    user_info=user_info, error_message=error_message, data=att_list)
        except ValueError as exc:
            error_message = str(exc)
    flash('Please Login First')
    return redirect('/')

@app.route('/query', methods=['POST', 'GET'])
def query():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    error_message = None
    result = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if (request.method == 'POST'):
                query = datastore_client.query(kind='Drivers')
                query_key = request.form['query_key']
                query.add_filter(query_key, '>=', request.form['query_value'])
                result = list(query.fetch())
                if result != []:
                    return render_template('query-driver.html', 
                            user_info=user_info, error_message=error_message, result=result)

                flash('No data available for that query!')
                return redirect('/query_driver')
            return render_template('query-driver.html', 
                    user_info=user_info, error_message=error_message)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('query-driver.html', 
            user_info=user_info, error_message=error_message)

@app.route('/query_team', methods=['POST', 'GET'])
def queryTeam():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    error_message = None
    result = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if (request.method == 'POST'):
                query = datastore_client.query(kind='Teams')
                query_key = request.form['query_key']
                query.add_filter(query_key, '>=', request.form['query_value'])
                result = list(query.fetch())
                if result != []:
                    return render_template('query-team.html', 
                            user_info=user_info, error_message=error_message, result=result)

                flash('No data available for that query!')
                return redirect('/query_team')
            return render_template('query-team.html', 
                    user_info=user_info, error_message=error_message)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('query-team.html', 
            user_info=user_info, error_message=error_message)

@app.route("/")
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
        except ValueError as exc:
            error_message = str(exc)

    return render_template('index.html', 
            error_message=error_message,
            user_info=user_info)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
