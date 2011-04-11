from google.appengine.ext import webapp
from google.appengine.ext import blobstore
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db
import os
import cgi
import urllib
import logging

from replay import Replay

class MainPage(webapp.RequestHandler):
	def get(self):
#       self.response.headers['Content-Type'] = 'text/plain'
		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'index.html')

		template_values = {
			'upload_url': upload_url
		}
		self.response.out.write(template.render(path, template_values))

class MainHandler(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        self.response.out.write('<html><body>')
        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit" 
            name="submit" value="Submit"> </form></body></html>""")



class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        self.redirect('/serve/%s' % blob_info.key())

		
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, replayid):
		resource = str(urllib.unquote(replayid))
		blob_info = blobstore.BlobInfo.get(replayid)
		self.send_blob(blob_info)


application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     (r'/(.*)', ServeHandler),
                                     ('/upload', UploadHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
