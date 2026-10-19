import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'services/morgenzeitung'))
import server
from core import Store
from http.server import ThreadingHTTPServer

class APITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        server.PREVIEW=False;server.TOKEN='unit-test-token-'+'x'*40;server.STORE=Store(Path(self.tmp.name)/'api.sqlite')
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.http.server_port)
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join()
    def request(self,path,data=None,token=True,origin=None):
        headers={'Authorization':'Bearer '+server.TOKEN} if token else {}
        if origin:headers['Origin']=origin
        if data is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        with urllib.request.urlopen(req) as r:return json.load(r)
    def test_unauthenticated_read_and_write_rejected(self):
        for path,data in [('/api/profile',None),('/api/feedback',{'text':'private'})]:
            with self.assertRaises(urllib.error.HTTPError) as err:self.request(path,data,False)
            self.assertEqual(err.exception.code,401)
    def test_wrong_origin_write_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as err:self.request('/api/feedback',{'text':'x'},origin='https://evil.example')
        self.assertEqual(err.exception.code,403)
    def test_feedback_survives_new_connection(self):
        self.assertTrue(self.request('/api/feedback',{'text':'test'})['saved'])
        self.assertEqual(Store(server.STORE.path).context()['feedback'][0]['text'],'test')
    def test_oversized_feedback_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as err:self.request('/api/feedback',{'text':'x'*4001})
        self.assertEqual(err.exception.code,400)
    def test_unknown_article_rating_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as err:self.request('/api/rating',{'id':'missing','value':1})
        self.assertEqual(err.exception.code,400)
if __name__=='__main__':unittest.main()
