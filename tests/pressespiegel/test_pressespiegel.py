import copy,json,unittest
from scripts.pressespiegel import validate,feedback_packet,MARKER
class PressespiegelTests(unittest.TestCase):
 def edition(self):
  return {'date':'2026-10-28','researched_at':'2026-10-28T07:00:00+01:00','kind':'researched','articles':[{'id':'abc','title':'Article','source':'Example','url':'https://example.org/article','published_at':'2026-10-28','summary':'Supported summary','basis':'teaser'}],'headlines':[]}
 def test_minimum_and_duplicates(self):
  ed=self.edition();validate(ed);row=copy.deepcopy(ed['articles'][0]);row['id']='def';row['url']+='?utm_source=test';ed['headlines']=[row]
  with self.assertRaises(ValueError):validate(ed)
 def test_private_fields_and_unsafe_urls(self):
  for key,value in [('source_excerpt','Private'),('url','javascript:alert(1)')]:
   ed=self.edition();ed['articles'][0][key]=value
   with self.assertRaises(ValueError):validate(ed)
 def test_import_requires_visible_provenance(self):
  ed=self.edition();ed['kind']='imported'
  with self.assertRaises(ValueError):validate(ed)
  ed.update(note='Imported archive',source_edition='/original');validate(ed)
 def test_feedback_replay_edit_and_test(self):
  def issue(n,comment='',test=False):return {'number':n,'title':'[Pressespiegel] Feedback 2026-10-28','updated_at':'2026-10-28T10:00:00Z','body':MARKER+json.dumps({'date':'2026-10-28','origin':'website-explicit','submission_id':str(n),'ratings':[],'comment':comment,'test':test})}
  first=feedback_packet([issue(1,'More context'),issue(2,test=True)],{})
  self.assertEqual(len(first['needs_reading']),1)
  self.assertFalse(feedback_packet([issue(1,'More context')],first['next_state'])['needs_reading'])
  edited=feedback_packet([issue(1,'Less context')],first['next_state'])
  self.assertEqual(edited['needs_reading'][0]['feedback']['comment'],'Less context')
  self.assertNotIn('weights',edited['next_state'])
 def test_duplicate_submission_is_one_context(self):
  payload={'date':'2026-10-28','origin':'website-explicit','submission_id':'same','ratings':[],'comment':'Hello'}
  items=[{'number':n,'title':'[Pressespiegel] Feedback 2026-10-28','body':MARKER+json.dumps(payload)} for n in [1,2]]
  self.assertEqual(len(feedback_packet(items,{})['needs_reading']),1)
