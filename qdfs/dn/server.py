import logging
import json
import os.path
from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.netutil import bind_sockets
from tornado.web import Application, RequestHandler, RedirectHandler
from tornado.httpserver import HTTPServer
from qdfs import netutils

class BaseHandler(RequestHandler):
    def hostify(self, path):
        # Just a silly thing because I hate trailing slashes
        path = os.path.join(self.root, path).strip('/')
        return 'http://%s:%d/%s' % (self.host, self.port, path)


class InfoHandler(BaseHandler):
    def initialize(self, fs, addr):
        self.root = '/info'
        self.fs = fs
        self.host, self.port = addr

    def get(self):
        response = {
            'info': self.fs.info(),
            'browse': self.hostify('/fs')
        }
        self.write(json.dumps(response))


class FSHandler(BaseHandler):
    def initialize(self, fs, addr):
        self.root = '/fs'
        self.fs = fs
        self.host, self.port = addr

    def get_file(self, path):
        # TODO: Is this actually necessary?
        path = path if path else '/'
        file = {}
        file['path'] = path
        file['exists'] = self.fs.exists(path)
        if file['exists']:
            file['stat'] = self.fs.stat(path)
            if path != '/':
                file['parent'] = self.hostify(os.path.dirname(file['path']).strip(os.path.sep))
        return file


    def get(self, path):
        file = self.get_file(path)
        if file['exists']:
            if self.fs.is_file(file['path']):
                file['type'] = 'file'
                file['contents'] = self.fs.read(file['path'])
            else:
                file['type'] = 'directory'
                files = self.fs.list(file['path'])
                files = map(lambda f: f.strip(os.path.sep), files)
                file['contents'] = map(self.hostify, files)
        else:
            self.set_status(404)

        self.write(json.dumps(file))

    def post(self, path):
        file = self.get_file(path)
        if file['exists']:
            self.set_status(409)
        else:
            if self.request.body:
                self.fs.create_file(file['path'])
                self.fs.write(file['path'], data=self.request.body)
            else:
                self.fs.create_dir(file['path'])

            self.set_status(201)

	self.set_header('Location', self.hostify(file['path']))
    
    def put(self, path):
        file = self.get_file(path)
        if file['exists']:
            if self.request.body:
                self.fs.write(file['path'], data=self.request.body)
                self.set_status(200)
            else:
                self.set_status(400)
        else:
            self.set_status(404)

	self.set_header('Location', self.hostify(file['path']))


class DataNodeServer(object):
    def __init__(self, fs, peer):
        self.fs = fs
        self.peer = peer

    def start(self):
        self.host = netutils.gethostname()
        sockets = bind_sockets(0)
        self.port = netutils.getport(sockets) 
       
        # Start peering
        self.peer.bind((self.host, self.port))
        self.peer.start()

        app = Application([
            (r'/', RedirectHandler, dict(url='/info')),
            (r'/info', InfoHandler, dict(fs=self.fs, addr=(self.host, self.port))),
            (r'/fs(/.+)*', FSHandler, dict(fs=self.fs, addr=(self.host, self.port))),
        ])
        server = HTTPServer(app)
        server.add_sockets(sockets)
        self.ioloop = IOLoop.current()
        addr = (self.host, self.port)
        self.ioloop.add_callback(logging.info, 'QDFS server listening @ http://%s:%d/' % addr)
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()

