import datetime
import random
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request, redirect
from google.auth.transport import requests

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


def store_time(dt, email):
	entity = datastore.Entity(key=datastore_client.key('User', email, 'visit'))
	entity.update({"timestamp": dt})
	datastore_client.put(entity)


def fetch_times(limit, email):
	ancestor_key = datastore_client.key('User', email);
	query = datastore_client.query(kind='visit', ancestor=ancestor_key);
	query.order = ["-timestamp"]
	times = query.fetch(limit=limit)
	return times

def retrieveUserInfo(claims):
	entity_key = datastore_client.key('UserInfo', claims['email'])
	entity = datastore_client.get(entity_key)
	return entity

def createUserInfo(claims):
	entity_key = datastore_client.key('UserInfo', claims['email'])
	entity = datastore.Entity(key = entity_key)

	entity.update({
		'email': claims['email'],
		'name': claims['name'],
		'address_list': []
		}) 
	datastore_client.put(entity)

def updateUserInfo(claims, new_string, new_int, new_float):
	entity_key = datastore_client.key('UserInfo', claims['email'])
	entity = datastore_client.get(entity_key)
	entity.update({
		'string_value': new_string,
		'int_value': new_int,
		'float_value': new_float
		})
	datastore_client.put(entity)

def retrieveAddresses(user_info):
	# make key objects out of all the keys and retrieve them
	address_ids = user_info['address_list']
	address_keys = []
	for i in range(len(address_ids)):
		address_keys.append(datastore_client.key('Address', address_ids[i]))

	address_list = datastore_client.get_multi(address_keys)
	return address_list

def createAddress(address1, address2, address3, address4):
	entity = datastore.Entity()
	entity.update({
		'address1': address1,
		'address2': address2,
		'address3': address3,
		'address4': address4
		})
	return entity

def addAddressToUser(user_info, address_entity):
	addresses = user_info['address_list']
	addresses.append(address_entity)
	user_info.update({
		'address_list': addresses
		})
	datastore_client.put(user_info)

def deleteAddress(claims, id):
	user_info = retrieveUserInfo(claims)
	address_list = user_info['address_list']
	del address_list[id]
	user_info.update({
		'address_list' : address_list
		})
	datastore_client.put(user_info)

@app.route('/delete_address/<int:id>', methods=['POST'])
def deleteAddressFromUser(id):
	id_token = request.cookies.get("token")
	error_message = None
	if id_token:
		try:
			claims = google.oauth2.id_token.verify_firebase_token(id_token,
					firebase_request_adapter)
			deleteAddress(claims, id)
		except ValueError as exc:
			error_message = str(exc)
	return redirect('/')

@app.route('/add_address', methods=['POST'])
def addAddress():
	id_token = request.cookies.get("token")
	claims = None
	user_info = None
	if id_token:
		try:
			claims = google.oauth2.id_token.verify_firebase_token(id_token,
					firebase_request_adapter)
			user_info = retrieveUserInfo(claims)
			address = createAddress(request.form['address1'],
					request.form['address2'], 
					request.form['address3'], 
					request.form['address4'])
			addAddressToUser(user_info, address)
		except ValueError as exc:
			error_message = str(exc)
	return redirect('/')

@app.route('/edit_user_info', methods=['POST'])
def editUserInfo():
	id_token = request.cookies.get("token")
	error_message = None
	claims = None
	user_info = None
	if id_token:
		try:
			claims = google.oauth2.id_token.verify_firebase_token(id_token,
					firebase_request_adapter)
			new_string = request.form['string_update']
			new_int = request.form['int_update']
			new_float = request.form['float_update']
			updateUserInfo(claims, new_string, new_int, new_float)
		except ValueError as exc:
			error_message = str(exc)

	return redirect("/")

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

	return render_template('index.html', user_data=claims, error_message=error_message,
			user_info=user_info)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080, debug=True)
