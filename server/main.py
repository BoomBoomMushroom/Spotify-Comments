import flask
import requests
import json
from flask import request
import os
import base64

app = flask.Flask(__name__)


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
    return responseMake("Backend for Spotify Comments"), 200


@app.route("/authorization_code")
def authorization_code():
    try:
        state = str(request.args.get('state'))
        code = str(request.args.get('code'))
        redirectURI = str(request.args.get('redirect_uri'))
        grantType = str(request.args.get('grant_type'))
    except:
        flask.abort(400)
        #return 400

    bothSpotifyStuff = os.environ['SPOTIFY_ID'] + ":" + os.environ[
        'SPOTIFY_SECRET']
    b64SpotifyAuth = base64.b64encode(
        bothSpotifyStuff.encode('utf-8')).decode('utf-8')

    urlParams = f"?grant_type={grantType}&redirect_uri={redirectURI}&code={code}&state={state}"
    result = requests.post(
        f"https://accounts.spotify.com/api/token{urlParams}",
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + b64SpotifyAuth
        })

    print(result.status_code)
    print(result.json())
    return responseMake(result.json()), 200


app.run(host="0.0.0.0", port=7777)
