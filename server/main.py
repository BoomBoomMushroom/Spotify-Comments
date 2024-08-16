from flask import Flask, redirect
import requests
import uuid

app = Flask(__name__)

URL = "https://api.spotify.com/v1/me/player/currently-playing"
CLIENT_ID = "5ee3aedb09a3447da667c5e06c276fb8"
CALLBACK_URL = "http://localhost:8888/callback"

scopes = 'user-read-private user-read-email'

#r = requests.get(URL, headers={"Authorization": ""})

#print(r.text)

@app.route("/")
def helloWorld():
    return "Hello world!"

@app.route("/auth")
def userAuth():
    state = str(uuid.uuid4())
    
    queryString = f"response_type=code&client_id={CLIENT_ID}&scope={scopes}&redirect_uri={CALLBACK_URL}&state={state}"
    redirectURL = f"https://accounts.spotify.com/authorize?{queryString}"
    a = redirect(redirectURL)
    print(a)
    #r = requests.get(redirectURL)
    
    #print(redirectURL)
    #print(r.text)
    return "stuff"

if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)