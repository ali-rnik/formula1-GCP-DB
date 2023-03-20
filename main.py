import datetime
import random
import time
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request, redirect, flash
from google.auth.transport import requests

app = Flask(__name__, static_url_path="/templates")

app.config["SECRET_KEY"] = "somesecretisagoodideatohaveprivacy"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False

datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

driver_att = [
		"name",
		"age",
		"pole-position",
		"wins",
		"points",
		"titles",
		"fastest-laps",
		"team",
		]
team_att = [
		"name",
		"year-found",
		"pole-position",
		"wins",
		"titles",
		"finished-position",
		]
att_list = {"driver": driver_att, "team": team_att}


def flash_redirect(message, path):
	flash(message)
	return redirect(path)

def get_session_info():
	id_token = request.cookies.get("token")
	claims = None
	err_msg = None
	if id_token:
		try:
			claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter, clock_skew_in_seconds=20)
		except ValueError as exc:
			err_msg = str(exc)
			return flash_redirect(err_msg, '/error')
		return claims
	return None


def retrieve_row(kind, name):
	key = datastore_client.key(kind, name)
	result = datastore_client.get(key)
	if result == None:
		return None
	return result.copy()


def update_row(kind, name):
	with datastore_client.transaction():
		key = datastore_client.key(kind, name)
		entity = datastore_client.get(key)
		for i in range(1, len(att_list[kind]), 1):
			entity[att_list[kind][i]] = request.form[att_list[kind][i]]
		datastore_client.put(entity)


def create_row(kind, name):
	key = datastore_client.key(kind, name)
	entity = datastore.Entity(key)
	obj = dict()
	for elem in att_list[kind]:
		obj[elem] = request.form[elem]
	entity.update(obj)
	datastore_client.put(entity)


def delete_row(kind, name):
	key = datastore_client.key(kind, name)
	datastore_client.delete(key)


def query_result(key, comp, val, kind):
	query = datastore_client.query(kind=kind)
	query.add_filter(key, comp, val)
	result = list(query.fetch())
	if result == []:
		return [None]
	result_list = []
	for item in result:
		result_list.append(item.copy())

	return result_list


def priority_taging(retreived, kind):
	for elem in att_list[kind]:
		tag1, tag2 = tag_returner(retreived[0][elem], retreived[1][elem], elem)
		retreived[0][elem], retreived[1][elem] = (retreived[0][elem], tag1), (
				retreived[1][elem],
				tag2,
				)
	print(retreived[0], "\n")
	print(retreived[1])

	return retreived


def tag_returner(a, b, col):
	if a == '':
		a = '0';
	if b == '':
		b = '0'

	lower_better = ["age", "finished-position", "year-found"]
	if col == "team" or col == "name":
		return "", ""
	if col in lower_better:
		if int(a, 36) > int(b, 36):
			return "down", "up"
		elif a == b:
			return "tie", "tie"
		else:
			return "up", "down"
	if int(a, 36) > int(b, 36):
		return "up", "down"
	elif a == b:
		return "tie", "tie"
	else:
		return "down", "up"


@app.route("/add/<kind>", methods=["POST", "GET"])
def add(kind):
	claims = get_session_info()
	print(claims)
	if claims:
		if request.method == "POST":
			if retrieve_row(kind, request.form["name"]) != None:
				return flash_redirect("Already Exist!", "/add/"+kind)

			create_row(kind, request.form["name"])
			return flash_redirect("Added Successfully.", "/add/"+kind)

		return render_template("add.html", claims=claims, data=att_list, kind=kind, pagename="Add "+kind)
	return flash_redirect("Please Login First", "/")

@app.route("/query", methods=["POST", "GET"])
def query():
	claims = get_session_info()

	if request.method == "GET":
		return render_template("query.html", claims=claims, data=att_list, pagename="Query Page")

	query_key = request.form["query_key"].split(".")
	result = query_result(query_key[1], ">=", request.form["query_value"], query_key[0])
	if result[0] == None:
		return flash_redirect("No data available for the Query", "/query");

	return render_template(
			"query.html", claims=claims, result=result, data=att_list, kind=query_key[0], pagename="Query Page"
			)


@app.route("/compare", methods=["POST", "GET"])
def compare():
	claims = get_session_info()
	kind = None
	result = None
	pagename = "Compare Page"

	if request.method == "GET":
		return render_template("compare.html", claims=claims, data=att_list, pagename=pagename)

	retreived = []
	retreived.append(
			query_result("name", "=", request.form["name1"], request.form["compare-kind"])[
				0
				]
			)
	retreived.append(
			query_result("name", "=", request.form["name2"], request.form["compare-kind"])[
				0
				]
			)

	if (
			retreived[0] == None
			or retreived[1] == None
			or retreived[0]["name"] == retreived[1]["name"]
			):
		return flash_redirect("Oooops! Wrong Comparison", "/compare");

	retreived = priority_taging(retreived, request.form["compare-kind"])
	return render_template(
			"compare.html",
			claims=claims,
			data=att_list,
			retreived=retreived,
			kind=request.form["compare-kind"],
			pagename=pagename
			)


@app.route("/update/<kind>/<name>", methods=["POST", "GET"])
def update(kind, name):
	claims = get_session_info()

	if not claims:
		return flash_redirect("Please Login First", "/query");

	if request.method == "POST":
		update_row(kind, name)
		return flash_redirect("Updated Successfully", "/query");

	result = retrieve_row(kind, name)
	return render_template(
			"update.html", claims=claims, result=result, data=att_list, kind=kind, pagename="Update Page"
			)


@app.route("/delete/<kind>/<name>")
def delete(kind, name):
	claims = get_session_info()

	if not claims:
		return flash_redirect("Please Login First", "/query");

	delete_row(kind, name)
	return flash_redirect("Deleted Successfully", "/query");


@app.route("/error")
def error():
	return render_template("50x.html")


@app.route("/")
def root():
	claims = get_session_info()
	return render_template("index.html", claims=claims, pagename="Homepage")


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080, debug=True)
