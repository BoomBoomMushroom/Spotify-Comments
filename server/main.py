import flask
import requests
import json
from flask import request
import os
import base64

app = flask.Flask(__name__)

bothSpotifyStuff = os.environ['SPOTIFY_ID'] + ":" + os.environ['SPOTIFY_SECRET']
b64SpotifyAuth = base64.b64encode(
    bothSpotifyStuff.encode('utf-8')).decode('utf-8')


def responseMake(r):
    try:
        json.dumps(r)
    except:
        pass
    resp = flask.Response(json.dumps(r))
    resp.headers['Access-Control-Allow-Origin'] = "*"
    return resp


@app.route("/")
def home():
    return responseMake("Backend for Spotify Comments"), 20


app.run(host="0.0.0.0", port=7777)
