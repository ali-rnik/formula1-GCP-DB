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


def get_session_info():
    id_token = request.cookies.get("token")
    claims = None
    err_msg = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter, clock_skew_in_seconds=30
            )
        except ValueError as exc:
            err_msg = str(exc)
            flash(err_msg)
            return redirect("/error", err_msg)
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
        tag1, tag2 = tag_returner(retreived[0][elem], retreived[1][elem], elem);
        retreived[0][elem], retreived[1][elem] = (retreived[0][elem], tag1), (retreived[1][elem], tag2)           
    print(retreived[0], "\n")
    print(retreived[1])

    return retreived

def tag_returner(a, b, col):
    lower_better = ['age', 'finished-position', 'year-found']
    if col == 'team' or col == 'name':
        return "", ""
    if col in lower_better:
        if int(a) > int(b):
            return "down", "up"
        elif a == b:
            return "tie", "tie"
        else:
            return "up", "down"
    if int(a) > int(b):
        return "up", "down"
    elif a == b:
        return "tie", "tie"
    else:
        return "down", "up"

@app.route("/add/<kind>", methods=["POST", "GET"])
def add(kind):
    claims = get_session_info()

    if claims:
        if request.method == "POST":
            if retrieve_row(kind, request.form["name"]) != None:
                flash("Already Exist!")
                return redirect("/add/" + kind)

            create_row(kind, request.form["name"])
            flash("Added Successfully.")
            return redirect("/add/" + kind)

        return render_template("add.html", claims=claims, data=att_list, kind=kind)

    flash("Please Login First")
    return redirect("/")


@app.route("/query", methods=["POST", "GET"])
def query():
    claims = get_session_info()

    if request.method == "GET":
        return render_template("query.html", claims=claims, data=att_list)

    query_key = request.form["query_key"].split(".")
    result = query_result(query_key[1], ">=", request.form["query_value"], query_key[0])
    if result[0] == None:
        flash("No data available for that query!")
        return redirect("/query")

    return render_template(
        "query.html", claims=claims, result=result, data=att_list, kind=query_key[0]
    )


@app.route("/compare", methods=["POST", "GET"])
def compare():
    claims = get_session_info()
    kind = None
    result = None

    if request.method == "GET":
        return render_template("compare.html", claims=claims, data=att_list)

    retreived = []
    retreived.append(query_result("name", "=", request.form["name1"], request.form["compare-kind"])[0])
    retreived.append(query_result("name", "=", request.form["name2"], request.form["compare-kind"])[0])

    if (
        retreived[0] == None
        or retreived[1] == None
        or retreived[0]["name"] == retreived[1]["name"]
    ):
        flash("Oooops! Wrong Comparison.")
        return redirect("/compare")

    retreived = priority_taging(retreived, request.form['compare-kind'])  
    return render_template(
        "compare.html",
        claims=claims,
        data=att_list,
        retreived=retreived,
        kind=request.form["compare-kind"],
    )


@app.route("/update/<kind>/<name>", methods=["POST", "GET"])
def update(kind, name):
    claims = get_session_info()

    if not claims:
        flash("Please Login First")
        return redirect("/query")

    if request.method == "POST":
        update_row(kind, name)
        flash("Updated Successfully")
        return redirect("/query")

    result = retrieve_row(kind, name)
    return render_template(
        "update.html", claims=claims, result=result, data=att_list, kind=kind
    )


@app.route("/delete/<kind>/<name>")
def delete(kind, name):
    claims = get_session_info()

    if not claims:
        flash("Please Login First")
        return redirect("/query")

    delete_row(kind, name)
    flash("Deleted Successfully")
    return redirect("/query")


@app.route("/error")
def error():
    return render_template("50x.html")


@app.route("/")
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter, clock_skew_in_seconds=30
            )
        except ValueError as exc:
            error_message = str(exc)

    return render_template("index.html", error_message=error_message, claims=claims)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
