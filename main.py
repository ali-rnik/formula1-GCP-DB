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

driver_att = ['name', 'age', 'number', 'pole-position', 'wins', 'points', 'titles', 'fastest-laps', 'team']
team_att = ['name', 'year-found', 'pole-position', 'wins', 'titles', 'finished-position']
att_list = {'driver': driver_att, 'team': team_att}

def get_session_info():
    id_token = request.cookies.get("token")
    claims = None
    err_msg = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter, clock_skew_in_seconds=30)
        except ValueError as exc:
          err_msg = str(exc)
          flash(err_msg)
          return redirect('/error', err_msg);

        return claims
    return None, None

def row_exist(name, kind):
    query = datastore_client.query(kind=kind)
    query.add_filter('name', '=', name)
    result = list(query.fetch())
    if result != []:
        return result
    return None

def update_row(name, kind):
    entity_key = datastore_client.key(kind, name)
    entity = datastore.Entity(key=entity_key)
    obj = dict()
    for elem in att_list[kind]:
        obj[elem] = request.form[elem];
    entity.update(obj)
    datastore_client.put(entity)
    
def get_query_result(query):
    result = list(query.fetch())
    if result == []:
        return None;
    result_list = []

    for item in result:
        result_list.append(item.copy())

    return result_list

@app.route('/add/<kind>', methods=['POST', 'GET'])
def add(kind):
    claims = get_session_info();
    
    if claims:
        if request.method == 'POST':
            if row_exist(request.form['name'], kind) != None:
                flash('Already Exist!')
                return redirect('/add/'+kind)

            update_row(request.form['name'], kind)
            flash('Added Successfully.')
            return redirect('/add/'+kind)

        return render_template('add.html', 
            claims=claims, data=att_list, kind=kind)

    flash('Please Login First')
    return redirect('/')

@app.route('/query', methods=['POST', 'GET'])
def query():
    claims = get_session_info();
    kind = None

    if (request.method == 'POST'):
        query_key = request.form['query_key'].split(".");
        kind = query_key[0]
        query = datastore_client.query(kind=kind)
        query.add_filter(query_key[1], '>=', request.form['query_value'])

        result = get_query_result(query);
        if not result:
            flash('No data available for that query!')
            return redirect('/query')
        
        return render_template('query.html', 
            claims=claims, result=result, data=att_list, kind=kind)

    return render_template('query.html', claims=claims, data=att_list)

@app.route('/update/<kind>/<name>', methods=['POST', 'GET'])
def update(kind, name):
    claims = get_session_info();
    
    if not claims:
        flash('Please Login First')
        return redirect('/query')
    
    if request.method == 'POST':
        update_row(name, kind)
        flash('Updated Successfully')
        return redirect('/query')
    
    query = datastore_client.query(kind=kind)
    query.add_filter('name', '=', name)
    
    result = get_query_result(query)[0]

    return render_template('update.html', 
        claims=claims, result=result, data=att_list, kind=kind)

@app.route('/error')
def error():
    return render_template('50x.html')

@app.route("/")
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                    firebase_request_adapter, clock_skew_in_seconds=30)
        except ValueError as exc:
            error_message = str(exc)

    return render_template('index.html', 
            error_message=error_message,
            claims=claims)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
