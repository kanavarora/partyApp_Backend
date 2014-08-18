import os
from flask import Flask, request, redirect, session
#from flask.ext.pymongo import PyMongo
import pymongo
import db
import datetime
from bson import json_util
import json
from grooveshark import Client
from grooveshark.classes.song import Song

import subprocess

app = Flask(__name__)
app.config['DEBUG'] = True
#mongo = PyMongo(app)
MONGO_URL = os.environ.get('MONGOHQ_URL')
 
if MONGO_URL:
    # Get a connection
    conn = pymongo.Connection(MONGO_URL)
    
    # Get the database
    db = conn[urlparse(MONGO_URL).path[1:]]
else:
    # Not on an app with the MongoHQ add-on, do some localhost action
    conn = pymongo.Connection('localhost', 27017)
    db = conn['someapps-db']


gsClient = Client()
gsClient.init()
gsClient.init_token()
gsClient.init_queue()

@app.route('/')
def hello():
    post = {"test" : "tes1"}
    db.abc.insert(post)
    return 'Hello World!'

@app.route('/ooh')
def hii():
    post_id = db.abc.find_one()
    return str(post_id)

@app.route('/downloadSong', methods=['POST'])
def downloadSong():
    song = Song.from_export(json.loads(request.form['song']), gsClient.connection)
    song.download(song_name = song.id + "-" + request.form['phoneNumber'])
    return song.id

'''
Creates a new song from the response and adds it to the db.
Also downloads the song. Response is a python data structure
'''
def addSong(response, phoneNumber):
    song = Song.from_export(response, gsClient.connection)
    newSong = {"phoneNumber" : phoneNumber,
               "date" : datetime.datetime.utcnow(),
               "link" : song.stream.url,
               "songId" : song.id,
               "songName" :song.name,
               "duration" : song.duration,
               "artistName" : song.artist.name,
               "playlist" : "default",
               "serialized" : song.export()}

    songId = db.songs.insert(newSong)
    return songId
    
    #download the song
    #return downloadSong(response)

@app.route('/addTwilioSong', methods=['POST'])
def addTwilioSong():
    return addSong(json.loads(request.form['song']), request.form['phoneNumber'])

'''
query - query for song to search
phoneNumber - phone number who is inputting that song

Gets the first song to search for and adds it to playlist db.
Downloads the song in ~/Music directory with name songId-phoneumber.mp3
'''
@app.route('/queryAndAddSong')
def inputSongqueryAndAddSong():
    songToSearch = request.values.get('query')
    phoneNumber = request.values.get('phoneNumber')
    found = False
    songToPlay = ""
    for song in gsClient.search(songToSearch, gsClient.SONGS):
        found = True
        songToPlay = song
        break
    if found:
        return addSong(songToPlay.export(), phoneNumber)
    else:
        return "Failed to find song"

'''
Adds a search song to the db
This is a post request. Assumes post has one key, which is song, which
is the exported version of Grooveshark.Song object
'''
@app.route('/addSearchSong', methods=['POST'])
def addSearchSong():
    addSong(json.loads(request.form['song']), "6666666666")
    return "success"

'''
query = Song to query for

Returns a jsoned response of list of songs in order which match the query.
A song returned has the following keys set
songId, songName, popularity, link, duration, artistName
'''
@app.route('/querySong')
def querySong():
    query = request.values.get('query')
    songs = gsClient.search(query, gsClient.SONGS)
    result = []
    for song in songs:
        result.append(song.export())
    return json.dumps(result)
    
'''
Drops the song collection.
TOOD: drop only by playlist, should same as deleting a playlist
'''
@app.route('/dropDb')
def dropDb():
    db.songs.drop()
    return "success"

'''
Gets the default playlist sorted in order of adding it to the queue.
Returns jsoned list of songs as they are store in db.
Key values for each song are:
phoneNumber, date, link, songId, duration, songName, artistName
Client can just play the song by finding the file (songId-phonNumber.mp3)
in Musics directory
'''
@app.route('/getPlayList')
def getPlayList():
    songs = db.songs.find({"playlist" : "default"}).sort("date", 1)
    res = []
    for song in songs:
        res.append(song)
    return json.dumps(res, default=json_util.default)

        
    


