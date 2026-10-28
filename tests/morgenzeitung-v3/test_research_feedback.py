import copy
import json
import unittest
from scripts.morgenzeitung_v3_engine import (topic_family, score, mark_recent_stories,
    evidence_guard, research_brief, MARKER, PREFIX)
from scripts.morgenzeitung_v3_release import prepare_edition

class ResearchFeedbackTests(unittest.TestCase):
    def test_export_removes_private_fields_at_every_level(self):
        row={'id':'a'*16,'url':'https://example.org/a','title':'A',
             'source_excerpt':'private','private_profile':{'x':1},'fit':5}
        edition={'date':'2026-10-29','articles':[row],'headlines':[],
                 'private_profile':{'x':1},'selection_audit':{'feedback_applied':False,'private':'secret'},
                 'new_sources':[{'name':'Example','private':'secret'}]}
        original=copy.deepcopy(edition)
        proof={'proofs':{row['id']:{'source_url':row['url'],'level':'teaser'}}}
        out=prepare_edition(edition,[row],proof)
        self.assertNotIn('private',json.dumps(out));self.assertNotIn('fit',out['articles'][0])
        self.assertEqual(out['articles'][0]['evidence_level'],'teaser')
        self.assertEqual(edition,original)
        edition['articles'][0]['title']={'private':'nested'}
        with self.assertRaises(ValueError):prepare_edition(edition,[row],proof)

    def test_ki_word_boundaries_and_explicit_aliases(self):
        profile={'topic_priorities':{'KI':5},'topic_aliases':{'Artificial intelligence':'KI'}}
        for topic in ['Pakistan','Kirche','Skifahren']:
            self.assertEqual(topic_family(topic,profile),topic)
        for topic in ['KI-Regulierung','KI','Artificial intelligence','Künstliche Intelligenz']:
            self.assertEqual(topic_family(topic,profile),'KI')

    def test_only_confirmed_publication_counts_as_covered(self):
        row={'id':'a'*16,'url':'https://example.org/a','title':'A','summary':'A fact.'}
        for preview in [True,None]:
            old={'date':'2026-10-28','preview':preview,'articles':[row]}
            self.assertFalse(mark_recent_stories([row],[old],'2026-10-29')[0].get('seen_recently',False))
        old['preview']=False
        self.assertTrue(mark_recent_stories([row],[old],'2026-10-29')[0]['seen_recently'])

    def test_editorial_fields_use_same_number_and_quote_checks(self):
        text='Wir prüften 999999 Quellen und fanden „ein Originalzitat“.'
        ed={'date':'2026-10-29','editorial_note':text}
        dossier={'schema_version':2,'edition_fields':{'editorial_note':[{
            'text':text,'supported':True,'source_excerpt':'Ein anderer Beleg ohne Zahl und Zitat.'}]}}
        codes={w['code'] for w in evidence_guard(ed,dossier)['warnings']}
        self.assertIn('NUMBER_MISMATCH',codes);self.assertIn('QUOTE_MISMATCH',codes)
        dossier['edition_fields']['editorial_note'][0]['source_excerpt']=text
        self.assertEqual(evidence_guard(ed,dossier)['warning_count'],0)

    def test_intrinsic_depth_without_feedback_and_news_unchanged(self):
        base={'fit':3,'novelty':3,'impact':3,'perspective':3}
        shallow={**base,'analysis_value':0,'context_value':0}
        deep={**base,'analysis_value':5,'context_value':5}
        self.assertGreater(score(deep,{}),score(base,{}))
        self.assertLess(score(shallow,{}),score(base,{}))
        self.assertEqual(score(deep,{},'Heute wichtig'),score(shallow,{},'Heute wichtig'))

    def test_brief_retains_original_free_text_and_context_without_interpreting(self):
        payload={'date':'2026-10-29','origin':'website-explicit','ratings':[
            {'id':'a'*16,'rating':'Nicht relevant','reason':'Das Thema passt, aber mir fehlt die Erklärung.'}],
            'comment':'Bitte mehr wirtschaftliche Mechanismen erklären.'}
        issue={'number':7,'title':PREFIX+payload['date'],'updated_at':'2026-10-29T08:00:00Z',
               'body':MARKER+json.dumps(payload)}
        test={**issue,'number':8,'body':MARKER+json.dumps({**payload,'test':True})}
        context={'a'*16:{'title':'Ein Klimabeitrag','topic':'Klima','summary':'Text'}}
        brief=research_brief({},[issue,test],context)
        self.assertEqual(brief['fresh_issue_numbers'],[7])
        self.assertEqual(brief['source_issues'][0]['body'],issue['body'])
        self.assertEqual(brief['article_context'],context)
        self.assertEqual(brief['explicit_reader_requests'][0]['text'],payload['comment'])
        self.assertEqual(brief['interpretation_status'],'requires_editorial_reading')
