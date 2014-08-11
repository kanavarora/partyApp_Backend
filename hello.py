import os
from flask import Flask, request, redirect, session
from flask.ext.pymongo import PyMongo
import db
import datetime
from bson import json_util
import json
from grooveshark import Client
from grooveshark.classes.song import Song

import subprocess

app = Flask(__name__)
app.config['DEBUG'] = True
mongo = PyMongo(app)


gsClient = Client()
gsClient.init()
gsClient.init_token()
gsClient.init_queue()

@app.route('/')
def hello():
    post = {"test" : "tes1"}
    mongo.db.abc.insert(post)
    return 'Hello World!'

@app.route('/ooh')
def hii():
    post_id = mongo.db.abc.find_one()
    return str(post_id)

'''
query - query for song to search
phoneNumber - phone number who is inputting that song

Gets the first song to search for and adds it to playlist db.
Downloads the song in ~/Music directory with name songId-phoneumber.mp3
'''
@app.route('/inputSong')
def inputSong():
    songToSearch = request.values.get('query')
    phoneNumber = request.values.get('phoneNumber')
    found = False
    songToPlay = ""
    for song in gsClient.search(songToSearch, gsClient.SONGS):
        found = True
        songToPlay = song
        break
    if found:
        newSong = {"phoneNumber" : phoneNumber,
                   "date" : datetime.datetime.utcnow(),
                   "link" : songToPlay.stream.url,
                   "songId" : songToPlay.id,
                   "songName" :songToPlay.name,
                   "duration" : songToPlay.duration,
                   "artistName" : songToPlay.artist.name,
                   "playlist" : "default",
                   "query" : request.values.get('query')}

        songId = mongo.db.songs.insert(newSong)

        #download the song
        songToPlay.download(song_name = songToPlay.id + "-" + phoneNumber)
        return songToPlay.id
    else:
        return "Failed to find song"

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
        jsoned_song = {"songId" : song.id,
                       "songName" : song.name,
                       "popularity" : song.popularity,
                       "link" : song.stream.url,
                       "duration" : song.duration,
                       "artistName" : song.artist.name}
        result.append(jsoned_song)
    return json.dumps(result)
    
'''
Drops the song collection.
TOOD: drop only by playlist, should same as deleting a playlist
'''
@app.route('/dropDb')
def dropDb():
    mongo.db.songs.drop()
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
    songs = mongo.db.songs.find({"playlist" : "default"}).sort("date", 1)
    res = []
    for song in songs:
        res.append(song)
    return json.dumps(res, default=json_util.default)

        
    


