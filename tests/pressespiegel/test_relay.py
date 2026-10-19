import importlib.util, pathlib, unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('relay',pathlib.Path(__file__).resolve().parents[2]/'services/feedback-relay/server.py')
relay=importlib.util.module_from_spec(spec);spec.loader.exec_module(relay)
class RelayTests(unittest.TestCase):
 def setUp(self):
  self.data={'date':'2026-10-19','ratings':[{'id':'a'*16,'value':'Sehr relevant','reason':'Mehr konkrete Zahlen.'}],'feedback':'Mehr Handelsblatt'}
 def test_schema(self):
  relay.validate(self.data)
  for field,value in [('ratings',self.data['ratings']*16),('feedback','x'*4001),('date','invalid')]:
   d=dict(self.data);d[field]=value
   with self.assertRaises(ValueError):relay.validate(d)
 def test_private_and_idempotent(self):
  rows=[]
  def api(path,data=None):
   if path=='':return {'private':True,'full_name':relay.REPO}
   if data is None:return rows
   rows.append(dict(data,number=1));return rows[0]
  with patch.object(relay,'github',side_effect=api):
   self.assertFalse(relay.save(self.data)['existing']);self.assertTrue(relay.save(self.data)['existing'])
  self.assertEqual(len(rows),1);self.assertIn('Mehr Handelsblatt',rows[0]['body'])
 def test_no_public_write(self):
  with patch.object(relay,'github',return_value={'private':False,'full_name':relay.REPO}) as api:
   with self.assertRaises(RuntimeError):relay.save(self.data)
   self.assertEqual(api.call_count,1)
 def test_failure_not_confirmed(self):
  with patch.object(relay,'github',side_effect=OSError('offline')):
   with self.assertRaises(OSError):relay.save(self.data)
if __name__=='__main__':unittest.main()
