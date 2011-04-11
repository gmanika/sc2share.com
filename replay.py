from google.appengine.ext import db

class Replay(db.Model):
	replayid = db.StringProperty(required=True)
	replaymd5 = db.StringProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	blobinfo = db.StringProperty()
	ip = db.StringProperty()



