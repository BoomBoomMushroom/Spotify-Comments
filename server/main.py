import flask
import json
from flask import request
from github import Github
import os
import requests
import threading
import uuid
import time

token = os.environ['github_token']

g = Github(token)
user = g.get_user()
apiRepo = user.get_repo("Spotify-Comments-API")

# Database

# per song
comments = {}


def syncGithubToDatabse():
    comments = requests.get(
        "https://raw.githubusercontent.com/BoomBoomMushroom/Spotify-Comments-API/main/comments.json"
    ).json()


def syncDatabaseToGithub():
    commentsFileHolder = apiRepo.get_contents("comments.json", "main")
    apiRepo.update_file(path=commentsFileHolder.path,
                        message="Updated comments from db",
                        content=json.dumps(comments, indent=4),
                        sha=commentsFileHolder.sha)

    print("Synced Database to Github")


syncGithubToDatabse()


def syncToGithub(firstPass=False):
    # Rate limit is 5,000 requests per hour
    # So lets call every 30 minutes
    threading.Timer(30 * 60, syncToGithub).start()

    if (firstPass):
        print("First pass! Don't sync")
        return
    print("Sync called!")
    syncDatabaseToGithub()


# Kickstart the process
syncToGithub(True)

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


def tokenToUserData(token):
    apiUrl = "https://api.spotify.com/v1/me"
    response = requests.get(apiUrl,
                            headers={"Authorization": "Bearer " + token})
    json = response.json()
    return json


"""
# Comment Example
[
    {
        "UUID": "UUID_DEMO",
        "SongTrackId": "SongTrackId",
        "user": {
            "username": "John Doe",
            "id": "USER_ID_DEMO",
            "profileURL": "https://spotify.com",
            "pfpURL": "https://i.scdn.co/image/ab6775700000ee85f4b8be4cfa24c9e067201f72"
        },
        "commentMeta": {
            "message": "Hello world!",
            "likes": [],
            "dislikes": [],
            "replyCount": 0,
            "replyingTo": null,
            "isEdited": false,
            "postTime": 0, // in seconds since epoch
        }
    }
]
"""


@app.route("/comments")
def getComments():
    try:
        songId = str(request.args.get('song_id'))
    except:
        flask.abort(400)
        #return 400

    result = []
    if songId in comments:
        result = comments[songId]

    return responseMake(result), 200


@app.route("/postcomment")
def postComment():
    try:
        message = str(request.args.get('message'))
        token = str(request.args.get('token'))
        songId = str(request.args.get('song_id'))

        #userId = str(request.args.get('user_id'))
        #username = str(request.args.get('username'))
        #pfpUrl = str(request.args.get('pfp_url'))
    except:
        flask.abort(400)
        #return 400

    userData = tokenToUserData(token)
    print(userData)

    return responseMake("out"), 200

    newComment = {
        "UUID": str(uuid.uuid4()),
        "SongTrackId": songId,
        "user": {
            "username": username,
            "id": userId,
            "profileURL": "https://open.spotify.com/user/" + userId,
            "pfpURL": pfpUrl
        },
        "commentMeta": {
            "message": message,
            "likes": [],
            "dislikes": [],
            "replyCount": 0,
            "replyingTo": None,
            "isEdited": False,
            "postTime": time.time(),
        }
    }

    if songId not in comments:
        comments[songId] = []

    comments[songId].append(newComment)
    # do this rn so I can get it to persist
    syncDatabaseToGithub()

    return responseMake(""), 200


app.run(host="0.0.0.0", port=7777)
