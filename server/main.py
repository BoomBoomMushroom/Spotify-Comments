import flask
from flask_cors import CORS
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

    print("Synced Github to Database")
    print(comments)


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
CORS(app,
     origins='*',
     headers=['Content-Type', 'Authorization'],
     expose_headers='Authorization')


def responseMake(r):
    try:
        json.dumps(r)
    except:
        pass
    resp = flask.Response(json.dumps(r))
    resp.headers.add('Access-Control-Allow-Origin', "*")
    return resp


def afterDatabaseChange():
    # do this rn so I can get it to persist
    syncDatabaseToGithub()


@app.route("/")
def home():
    return responseMake("Backend for Spotify Comments"), 200


def tokenToUserData(token):
    apiUrl = "https://api.spotify.com/v1/me"
    response = requests.get(apiUrl, headers={"Authorization": token})
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
    if request.method == "OPTIONS":
        return responseMake(""), 200

    try:
        message = str(request.args.get('message'))
        songId = str(request.args.get('song_id'))
    except:
        flask.abort(400)
        #return 400

    msgLen = len(message)
    if msgLen > 1000 or msgLen <= 0:
        return responseMake("Message is too long"), 400

    auth = request.headers.get("Authorization")
    userData = tokenToUserData(auth)

    try:
        username = userData["display_name"]
        userId = userData["id"]

        validPfps = [x for x in userData["images"] if x['width'] == 300]
        pfp = validPfps[0]
        pfpUrl = pfp["url"]
    except:
        flask.abort(500)

    if songId not in comments:
        comments[songId] = []

    newUUID = str(uuid.uuid4())
    sameUUID = [x for x in comments[songId] if x['UUID'] == newUUID]
    failsafeTriesLeft = 100_000

    while len([x for x in comments[songId] if x['UUID'] == newUUID]) > 0:
        if failsafeTriesLeft <= 0:
            flask.abort(508)

        newUUID = str(uuid.uuid4())
        failsafeTriesLeft -= 1

    newComment = {
        "UUID": newUUID,
        "SongTrackId": songId,
        "user": {
            "username": username,
            "id": userId,
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

    comments[songId].append(newComment)
    afterDatabaseChange()

    return responseMake("Success!"), 200


@app.route("/react")
def reactToComment():
    if request.method == "OPTIONS":
        return responseMake(""), 200

    try:
        # "likes" or "dislikes"
        reactType = str(request.args.get('react_type'))
        commentId = str(request.args.get('comment_id'))
        songId = str(request.args.get('song_id'))
    except:
        flask.abort(400)
        #return 400

    auth = request.headers.get("Authorization")
    userData = tokenToUserData(auth)

    try:
        userId = userData["id"]
    except:
        flask.abort(500)

    def removeFromList(list, item):
        if item in list:
            list.remove(item)

    try:
        songComments = comments[songId]
        commentData = [x for x in songComments if x['UUID'] == commentId][0]
    except:
        flask.abort(500)

    if reactType == "like": reactType = "likes"
    elif reactType == "dislike": reactType = "dislikes"

    antiReact = "likes" if reactType == "dislikes" else "dislikes"
    commentMeta = commentData["commentMeta"]

    if reactType == " ":
        removeFromList(commentMeta["likes"], userId)
        removeFromList(commentMeta["dislikes"], userId)
    else:
        if userId in commentMeta[reactType]:
            removeFromList(commentMeta[reactType], userId)
        else:
            commentMeta[reactType].append(userId)
            removeFromList(commentMeta[antiReact], userId)

    afterDatabaseChange()

    return responseMake("Success!"), 200


app.run(host="0.0.0.0", port=7777)
