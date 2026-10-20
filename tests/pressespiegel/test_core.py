import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'services/morgenzeitung'))
from core import Store, article_id, schedule, instant, canonical
from research import run

class PaperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'paper.db';self.store=Store(self.path)
        self.ed=json.loads((Path(__file__).resolve().parents[2]/'services/morgenzeitung/preview.json').read_text())
    def test_durable_rating_change_and_no_known_penalty(self):
        self.store.publish(self.ed);aid=article_id(self.ed['articles'][0]['url'])
        self.store.rate(aid,-1,'Schon bekannt')
        self.assertEqual(Store(self.path).ratings()[aid]['value'],-1)
        self.assertEqual(self.store.learning()['Wirtschaft & Budget'],0)
        self.store.rate(aid,1,'Mehr davon')
        self.assertEqual(len(self.store.ratings()),1)
        self.assertGreater(self.store.learning()['Wirtschaft & Budget'],0)
        self.assertLess(self.store.learning()['Wirtschaft & Budget'],.1)
    def test_dst(self):
        self.assertEqual(schedule('2026-10-24')[1].hour,5)
        self.assertEqual(schedule('2026-10-25')[1].hour,6)
        self.assertEqual(schedule('2027-03-27')[1].hour,6)
        self.assertEqual(schedule('2027-03-28')[1].hour,5)
    def test_not_published_early(self):
        self.store.publish(self.ed)
        self.assertEqual(self.store.list_editions('2026-10-18T13:44:00Z'),[])
        self.assertEqual(len(self.store.list_editions('2026-10-18T14:00:00Z')),1)
    def test_idempotent(self):
        self.assertTrue(self.store.publish(self.ed))
        # Idempotence checked before validation of historical links.
        self.assertFalse(self.store.publish(self.ed))
        self.assertEqual(len(self.store.list_editions('2026-10-20T00:00:00Z')),1)
    def test_same_event_and_tracking_duplicate(self):
        self.ed['articles'][1]['event']=self.ed['articles'][0]['event']
        with self.assertRaises(ValueError):self.store.publish(self.ed)
        self.assertEqual(canonical('https://orf.at/stories/1/?utm_source=x'),canonical('https://orf.at/stories/1/'))
    def test_no_duplicate_across_sections_in_new_edition(self):
        e=copy.deepcopy(self.ed);e['preview']=False
        for a in e['articles']:
            if a.get('kind') == 'Nachricht':
                a['kind']='Analyse'
        with self.assertRaisesRegex(ValueError,'beiden Rubriken'):
            self.store.publish(e)
    def test_long_reads_are_not_short_news(self):
        e=copy.deepcopy(self.ed);e['preview']=False
        with self.assertRaisesRegex(ValueError,'Kurznachrichten'):
            self.store.publish(e)
    def test_old_article_rejected(self):
        self.ed['window_start']='2026-10-17T14:00:00Z'
        with self.assertRaises(ValueError):self.store.publish(self.ed)
    def test_profile_conflict(self):
        p=self.store.profile();self.store.save_profile(p)
        with self.assertRaises(ValueError):self.store.save_profile(p)
        self.assertEqual(len(self.store.context()['profile_changes']),1)
    def next_edition(self):
        data=copy.deepcopy(self.ed)
        for section in ('articles','headlines'):
            for i,a in enumerate(data[section]):
                a.update(url='https://example.com/'+section+str(i),published_at='2026-10-19T05:00:00Z',event=section+str(i),title='Neue Meldung '+section+str(i))
        return data
    def test_feedback_is_input_to_later_selection(self):
        self.store.publish(self.ed);self.store.feedback('Mehr über Bildung')
        seen={}
        def fetch(ctx,start,end):
            seen.update(ctx);return self.next_edition()
        self.assertTrue(run(self.store,'2026-10-19',fetch,'2026-10-19T05:15:00Z'))
        self.assertEqual(seen['feedback'][0]['text'],'Mehr über Bildung')
        self.assertEqual(self.store.edition(at='2026-10-19T06:00:00Z')['feedback_ids'],[1])
        self.assertEqual(self.store.edition(at='2026-10-19T06:00:00Z')['window_start'],self.ed['window_end'])
        self.assertFalse(run(self.store,'2026-10-19',fetch,'2026-10-19T06:00:00Z'))
    def test_failed_research_preserves_latest_and_caps_retries(self):
        self.store.publish(self.ed)
        def fail(*args):raise RuntimeError('offline')
        for hour in (6,7,8):
            with self.assertRaises(RuntimeError):run(self.store,'2026-10-19',fail,f'2026-10-19T0{hour}:00:00Z')
        self.assertFalse(run(self.store,'2026-10-19',fail,'2026-10-19T09:00:00Z'))
        self.assertEqual(self.store.edition(at='2026-10-20T00:00:00Z')['date'],'2026-10-18')
    def test_followup_requires_new_facts(self):
        self.store.publish(self.ed);d=self.next_edition();d.update(date='2026-10-19',window_start=self.ed['window_end'],window_end='2026-10-19T05:15:00Z',available_at='2026-10-19T05:45:00Z')
        d['articles'][0].update(event=self.ed['articles'][0]['event'],facts=self.ed['articles'][0]['facts'],novelty='Neue Überschrift')
        with self.assertRaises(ValueError):self.store.publish(d)
        d['articles'][0]['facts'].append('Eine neue Entscheidung');self.assertTrue(self.store.publish(d))
if __name__=='__main__':unittest.main()
