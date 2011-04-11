#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib

from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from urlparse import urlparse
from urllib import urlencode, unquote, quote

from replay import Replay

from hashlib import md5

from counter import get_count, increment, counter_as_string

class MainHandler(webapp.RequestHandler):
	def get(self):
		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Pragma'] = 'no-cache'

		template_values = {
                        'upload_url': upload_url,
			'counter': counter_as_string('principal')
		}
		self.response.out.write(template.render(path, template_values))

class InfoHandler(webapp.RequestHandler):
	def get(self, resource):
		query = Replay.all()
                query.filter('replayid =', resource)

                results = query.fetch(1)

                if results:
			num_results = len(results)
                        result = results[0]
                        blob_info = blobstore.BlobInfo.get(result.blobinfo)
			original_filename = blob_info.filename
			filesize = blob_info.size
			dl_count = get_count(resource)
		else:
			num_results = 0
			original_filename = ""
			filesize = ""
			dl_count = 0

		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'info.html')
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Pragma'] = 'no-cache'

		template_values = {
                        'upload_url': upload_url,
			'counter': counter_as_string('principal'),
			'resource': resource,
			'num_results': num_results,
			'original_filename': original_filename,
			'filesize': filesize,
			'dl_count': dl_count,
		}
		self.response.out.write(template.render(path, template_values))

class AboutHandler(webapp.RequestHandler):
	def get(self):
		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'about.html')
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Pragma'] = 'no-cache'

		template_values = {
                        'upload_url': upload_url
		}
		self.response.out.write(template.render(path, template_values))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
	if not upload_files:
		self.redirect('/failed/nofile/')
		return
        blob_info = upload_files[0]
	key = blob_info.key()
	if blob_info.size > 1048576:
		blob_info.delete()
	        self.redirect('/failed/sizeerror/%s' % blob_info.filename)
		return
	blob_reader = blobstore.BlobReader(key)
	magic = blob_reader.read(50)
	if magic[0:3] != "MPQ" or not "StarCraft II replay" in magic:
		blob_info.delete()
	        self.redirect('/failed/typeerror/%s' % blob_info.filename)
		return


	replayid = counter_as_string('principal')
	increment('principal')

	m = md5()
	m.update(blob_reader.read(blob_info.size))
	replaymd5 = m.hexdigest()
	
	replay = Replay(replayid=replayid, replaymd5 = replaymd5, blobinfo = str(key), ip=self.request.remote_addr)
	replay.put()

        self.redirect('/success/%s' % replayid)

class SuccessHandler(webapp.RequestHandler):
	def get(self, replayid=1):
		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'success.html')
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Pragma'] = 'no-cache'

		baseurl = urlparse(self.request.url).netloc;

		# Remover www
		if "sc2share.com" in baseurl:
			baseurl = "sc2shr.com"

		template_values = {
			'upload_url': upload_url,
			'baseurl': baseurl,
			'replayid': replayid
		}
		self.response.out.write(template.render(path, template_values))
		
class FailureHandler(webapp.RequestHandler):
	def get(self, reason, filename):
		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'failure.html')
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Pragma'] = 'no-cache'

		failure_reasons = {}
		failure_reasons['pt'] = {
			'typeerror': 'O arquivo que você enviou não é um arquivo de replay do Starcraft.',
			'sizeerror': 'O arquivo que você enviou é muito grande.',
			'nofile': 'Nenhum arquivo chegou aqui. Você lembrou de escolher um arquivo antes de clicar em Enviar?'
		}
		failure_reasons['en'] = {
			'typeerror': 'File is not a Starcraft replay file.',
			'sizeerror': 'File is too large.',
			'nofile': 'No file was uploaded. Did you select a file to upload?'
		}

		template_values = {
			'upload_url': upload_url,
			'filename': unquote(filename).decode('utf-8'),
			'errormsg': failure_reasons['en'][reason]
		}
		self.response.out.write(template.render(path, template_values))


class DoServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, resource, extension):
		query = Replay.all()
		query.filter('replayid =', resource)

		results = query.fetch(1)

		if results:
			result = results[0]
			blob_info = blobstore.BlobInfo.get(result.blobinfo)
			increment(resource)
			self.send_blob(blob_info)
			return

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, resource, extension=".SC2Replay"):
		if resource[-10:] in (".SC2Replay", ".sc2replay"):
			resource = resource[0:-10]
		query = Replay.all()
		query.filter('replayid =', resource)

		results = query.fetch(1)

		if results:
			result = results[0]
			blob_info = blobstore.BlobInfo.get(result.blobinfo)
			if blob_info:
				self.redirect('/d/%s/%s' % (resource, quote(blob_info.filename.encode("utf-8"))))
				return
			else:
				reason = 'nosuchfile'
		else:
			reason = 'nosuchfile'

		upload_url = blobstore.create_upload_url('/upload')
		path = os.path.join(os.path.dirname(__file__), 'nofetch.html')
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Pragma'] = 'no-cache'

		failure_reasons = {}
		failure_reasons['pt'] = {
			'nosuchfile': 'O arquivo pedido não existe. Pode ser que ele nunca tenha existido, pode ser que ele tenha sido apagado, e pode ser que algo catastrófico tenha acontecido. Difícil dizer o que foi.'
		}
		failure_reasons['en'] = {
			'nosuchfile': 'The requested file does not exist. Maybe it never existed, maybe it has been deleted, maybe something catastrophic happened. In any case, we apologize.'
		}
		
		template_values = {
			'upload_url': upload_url,
			'errormsg': failure_reasons['en'][reason]
		}
		self.response.out.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication(
          [('/', MainHandler),
           ('/upload', UploadHandler),
           ('/success/(.*)', SuccessHandler),
           ('/failed/(.*)/(.*)', FailureHandler),
           ('/info/(.*)', InfoHandler),
           ('/about', AboutHandler),
           ('/d/(.*)/(.*)', DoServeHandler),
           ('/([^/]+)?', ServeHandler),
          ], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
  main()
