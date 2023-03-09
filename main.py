import datetime
import random
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request, redirect, flash
from google.auth.transport import requests

app = Flask(__name__)

app.config['SECRET_KEY'] = "somesecretisagoodideatohaveprivacy" 
app.config['SESSION_TYPE'] = 'filesystem' 
app.config['SESSION_PERMANENT']= False

datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()

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
    info_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if (request.method == 'POST'):
                query = datastore_client.query(kind='Drivers')
                query.add_filter('name', '=', request.form['name'])
                result = list(query.fetch())
                print(result);
                if result != []:
                    flash('Driver Already Exist!')
                    return redirect('/add_driver')
                entity_key = datastore_client.key('Drivers', request.form['name'])
                entity = datastore.Entity(key=entity_key)
                entity.update({
                    'name': request.form['name'],
                    'age': request.form['age'],           
                    'pole_position': request.form['pole_position'],
                    'wins': request.form['wins'],
                    'points' : request.form['points'],
                    'titles': request.form['titles'],
                    'fastest_laps': request.form['fastest_laps'],
                    'team': request.form['team']})
                datastore_client.put(entity)
                flash('Driver added Successfully!')
                return redirect('/add_driver')
            return render_template('add-driver.html', 
                user_info=user_info, error_messasge=error_message)
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
    info_message = None
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
                entity.update({
                    'name': request.form['name'],
                    'year_fnd': request.form['year_fnd'],           
                    'pole_position': request.form['pole_position'],
                    'wins': request.form['wins'],
                    'titles': request.form['titles'],
                    'finish_position': request.form['finish_position']})
                datastore_client.put(entity)
                flash('Team added Succesfully!')
                return redirect('/add_team')
            return render_template('add-team.html', 
                user_info=user_info, error_message=error_message)
        except ValueError as exc:
            error_message = str(exc)
    flash('Please Login First')
    return redirect('/')



@app.route('/query_driver', methods=['GET'])
def queryDriverPage():
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
        except ValueError as exc:
            error_message = str(exc)

    return render_template('query-driver.html', 
            error_message=error_message,
            user_info=user_info)

@app.route('/query_driver', methods=['Post'])
def queryDriver():
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
        except ValueError as exc:
            error_message = str(exc)

    query = datastore_client.query(kind='Teams')
    query.add_filter('name', '>=', request.form['name'])
    #query.add_filter('age', '>=', request.form['age'])
    #query.add_filter('pole_position', '>=', request.form['pole_position'])
    #query.add_filter('wins', '>=', request.form['wins'])
    #query.add_filter('titles', '>=', request.form['titles'])
    #query.add_filter('fastest_laps', '>=', request.form['fastest_laps'])
    #query.add_filter('team', '=', request.form['team'])
    result = query.fetch()

    return render_template('query-driver.html', 
            error_message=error_message,
            user_info=user_info,
            result=result)

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
