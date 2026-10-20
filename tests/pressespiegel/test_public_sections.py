"""Verify published editions never place one story in both sections."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'services/morgenzeitung'))
from core import canonical, similar

def validate_sections(edition):
    """Fail closed on duplicate URLs, event IDs and near-identical titles."""
    seen_urls=set()
    seen_events=set()
    titles=[]
    for section in ('headlines','articles'):
        for article in edition[section]:
            url=canonical(article['url'])
            event=article['event']
            title=article['title']
            if url in seen_urls or event in seen_events or any(similar(title,t) for t in titles):
                raise ValueError(f"Same story appears multiple times in {edition['date']}: {title}")
            seen_urls.add(url)
            seen_events.add(event)
            titles.append(title)

class PublishedSectionTests(unittest.TestCase):
    def setUp(self):
        self.ed=json.loads((ROOT/'Privat/Pressespiegel/data/2026-10-18.json').read_text())
    def test_all_public_editions_are_nonoverlapping(self):
        index=json.loads((ROOT/'Privat/Pressespiegel/data/index.json').read_text())
        for day in index['dates']:
            with self.subTest(date=day):
                edition=json.loads((ROOT/'Privat/Pressespiegel/data'/f'{day}.json').read_text())
                self.assertEqual(edition['date'],day)
                validate_sections(edition)
    def test_latest_demo_is_split_into_nonoverlapping_sections(self):
        validate_sections(self.ed)
        self.assertEqual(len(self.ed['headlines']),3)
        self.assertEqual(len(self.ed['articles']),2)
    def test_url_duplicates_rejected_even_with_utm_parameter(self):
        modified=copy.deepcopy(self.ed)
        modified['headlines'][0]['url']=modified['articles'][0]['url']+'?utm_source=newsletter'
        with self.assertRaisesRegex(ValueError,'Same story'):validate_sections(modified)
    def test_event_duplicates_rejected_even_different_source_url(self):
        modified=copy.deepcopy(self.ed)
        modified['headlines'][0]['event']=modified['articles'][0]['event']
        with self.assertRaisesRegex(ValueError,'Same story'):validate_sections(modified)
    def test_title_duplicates_rejected_even_different_event(self):
        modified=copy.deepcopy(self.ed)
        modified['headlines'][0]['title']=modified['articles'][0]['title']
        with self.assertRaisesRegex(ValueError,'Same story'):validate_sections(modified)

if __name__=='__main__':
    unittest.main()
