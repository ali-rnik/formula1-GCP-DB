import datetime
import random
import time
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

@app.route('/add/<kind>', methods=['POST', 'GET'])
def add(kind):
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
                query = datastore_client.query(kind=kind)
                query.add_filter('name', '=', request.form['name'])
                result = list(query.fetch())
                if result != []:
                    flash(kind + ' Already Exist!')
                    return redirect('/add/'+kind)
                entity_key = datastore_client.key(kind, request.form['name'])
                entity = datastore.Entity(key=entity_key)
                obj = dict()
                for elems in att_list[kind+"_att"]:
                    obj[elems[0]] = request.form[elems[0]];
                entity.update(obj)
                datastore_client.put(entity)
                flash(kind + ' added Succesfully!')
                return redirect('/add/'+kind)
            return render_template('add.html', 
                    user_info=user_info, error_message=error_message, data=att_list[kind+"_att"], kind=kind)
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
        except ValueError as exc:
            error_message = str(exc)

    if (request.method == 'POST'):
        query_key = request.form['query_key'].split(".");
        query = datastore_client.query(kind=query_key[0])
        query.add_filter(query_key[1], '>=', request.form['query_value'])
        result = list(query.fetch())
        if result != []:
            result_map = {};
            result_map['kind'] = result[0].kind;
            result_map['items'] = [];
            for item in result:
                    item_sorted = sorted(list(item.items()), key= lambda x: x[0])
                    result_map['items'].append(sorted(item_sorted, key=lambda x: x[0] != 'name'));
            result_map['count'] = len(result_map['items']);
        
            return render_template('query.html', 
                    user_info=user_info, error_message=error_message, result=result_map, data=att_list)

        flash('No data available for that query!')
        return redirect('/query')
    return render_template('query.html', 
               user_info=user_info, error_message=error_message, data=att_list)


    return render_template('query.html', 
            user_info=user_info, error_message=error_message, data=att_list)

@app.route("/")
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter, clock_skew_in_seconds=3)

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
