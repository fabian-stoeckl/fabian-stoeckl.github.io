import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.morgenzeitung_v3_engine import score,select,evidence_guard,ingest_feedback
from scripts.morgenzeitung_v3_editorial import reason_labels,editorial_mix_report
from scripts.morgenzeitung_v3_release import prepare_edition
from scripts.morgenzeitung_v3_audit import before_snapshot,learning_result
from scripts.morgenzeitung_v3_private_ci import changed_dates,verify_changed,public_edition_paths


def candidate(n=1,**kw):
    return {"id":f"{n:016x}","title":"Original report","source":"Publisher",
            "url":f"https://example.org/{n}","topic":"Industry","fit":3,
            "novelty":3,"impact":3,"perspective":3,**kw}


class AuditFixes(unittest.TestCase):
    def test_praise_negation_and_quoted_criticism_do_not_create_negative_signal(self):
        for reason in ('Nicht zu oberflächlich, gute Gegenposition.',
                       'Nicht einseitig', 'Der Autor nennt es "zu oberflächlich"',
                       'Gute andere Perspektive', 'Ich fand es nicht zu speziell'):
            self.assertEqual(reason_labels(reason,'Sehr relevant'),(),reason)
        self.assertEqual(set(reason_labels('Schon bekannt und zu oberflächlich','Teilweise relevant')),
                         {'already_known','too_shallow'})

    def test_structured_choices_override_prose_and_survive_ingestion(self):
        self.assertEqual(reason_labels('Nicht zu oberflächlich','Sehr relevant',['more_of_this']),('more_of_this',))
        payload={'date':'2026-10-28','origin':'website-explicit','ratings':[
            {'id':'a'*16,'rating':'Sehr relevant','reason':'Unveränderter Lesertext',
             'reason_codes':['too_shallow','INVALID'],'section':'Vertiefungen'}]}
        issue={'number':1,'title':'[Morgenzeitung 3] Feedback 2026-10-28','updated_at':'2026-10-28T10:00:00Z',
               'body':'MORGENZEITUNG_V3_FEEDBACK_V1\n'+json.dumps(payload)}
        result,_=ingest_feedback({},[issue],{'a'*16:'Industry'})
        self.assertEqual(result['article_feedback']['a'*16]['reason_codes'],['too_shallow'])
        self.assertEqual(result['feedback_dimensions']['counts']['too_shallow'],1)

    def test_topic_novelty_does_not_erase_general_depth(self):
        row=candidate(analysis_value=5)
        general={'style_preference_signals':{'analysis':2}}
        specific={**general,'topic_style_signals':{'Industry':{'novelty':1,'analysis':0}}}
        self.assertEqual(score(row,specific),score(row,general)+.5)

    def test_no_zero_quality_filler_and_explicit_editorial_rejection(self):
        self.assertEqual(select([candidate(fit=0,novelty=0,impact=0,perspective=0)],{}),[])
        self.assertEqual(select([candidate(editorial_eligible=False)],{}),[])
        self.assertEqual(len(select([candidate()],{},limit=12)),1)

    def test_research_report_requests_alternatives_and_austrian_research(self):
        pool=[candidate(i,region='International') for i in range(1,16)]
        report=editorial_mix_report(pool,pool[:14],section='Heute wichtig')
        self.assertTrue(any('Thin candidate' in x for x in report['recommendations']))
        self.assertTrue(any('Austria' in x for x in report['recommendations']))
        self.assertFalse(report['release_blocked'])

    def test_extra_claims_need_actual_field_evidence(self):
        row=candidate(summary='Eine belegte Aussage.',why_selected='900 Millionen Euro werden eingespart.')
        proof={'source_url':row['url'],'level':'read','claims':[
            {'text':row['summary'],'source_excerpt':row['summary'],'supported':True}]}
        ed={'articles':[row]};d={'proofs':{row['id']:proof}}
        report=evidence_guard(ed,d)
        self.assertTrue(any(x['code']=='UNCOVERED_FIELD' for x in report['warnings']))
        proof['fields']={'why_selected':[{'text':row['why_selected'],'source_excerpt':'Eine Einsparung ohne konkrete Zahlen.','supported':True}]}
        self.assertTrue(any(x['code']=='NUMBER_MISMATCH' for x in evidence_guard(ed,d)['warnings']))

    def test_future_identity_and_evidence_levels_cannot_be_omitted(self):
        row=candidate(summary='Eine belegte Aussage.',published_at='2026-10-29')
        d={'proofs':{row['id']:{'source_url':row['url'],'level':'teaser','claims':[
            {'text':row['summary'],'source_excerpt':row['summary'],'supported':True}]}}}
        report=evidence_guard({'date':'2026-10-29','articles':[row]},d)
        self.assertTrue(any(x['code']=='EVIDENCE_LEVEL_MISMATCH' for x in report['warnings']))
        self.assertTrue(any(x.get('field')=='published_at' for x in report['warnings']))

    def test_export_keeps_known_metadata_without_leaking_private_fields(self):
        row=candidate(article_type='analysis',source_excerpt='PRIVATE',private_rating='PRIVATE')
        edition={'articles':[{k:row[k] for k in ('id','url','title','source')}],'headlines':[]}
        dossier={'proofs':{row['id']:{'source_url':row['url'],'level':'teaser'}}}
        out=prepare_edition(edition,[row],dossier)
        self.assertEqual(out['articles'][0]['evidence_level'],'teaser')
        self.assertEqual(out['articles'][0]['article_type'],'analysis')
        self.assertNotIn('PRIVATE',json.dumps(out))
        self.assertNotIn('fit',out['articles'][0])

    def test_special_edition_is_detected_and_unregistered_path_rejected(self):
        path='Privat/Persoenliche-Zeitung/extra/data/2026-10-29.json'
        self.assertEqual(changed_dates([path]),['2026-10-29'])
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'Unregistered'):
                verify_changed(root,[path],'',fetcher=lambda *_:self.fail('must not fetch'))

    def test_all_live_editions_have_public_receipts(self):
        from scripts.morgenzeitung_v3_release import check_public_receipt
        paths=public_edition_paths('.')
        self.assertEqual(len(paths),2)
        for path in paths:self.assertEqual(check_public_receipt(json.loads(path.read_text())),[])

    def test_snapshot_replays_actual_limits_and_rejects_code_changes(self):
        pool={'articles':[candidate(i) for i in range(1,15)],'headlines':[candidate(i) for i in range(20,38)]}
        settings={'articles':{'limit':12,'discovery_slots':0,'min_score':15},
                  'headlines':{'limit':15,'discovery_slots':0,'min_score':15}}
        snap=before_snapshot(pool,{},'2026-10-29',selection=settings)
        report=learning_result(snap,{})
        self.assertEqual(len(report['comparison']['Vertiefungen']['before_ids']),12)
        self.assertEqual(len(report['comparison']['Heute wichtig']['before_ids']),15)
        self.assertFalse(report['comparison']['Vertiefungen']['feedback_received'])
        with patch('scripts.morgenzeitung_v3_audit.engine_identity',return_value={'files':{}}):
            with self.assertRaisesRegex(ValueError,'frozen engine'):learning_result(snap,{})
        with self.assertRaisesRegex(ValueError,'parameters required'):before_snapshot(pool,{},'2026-10-29')
