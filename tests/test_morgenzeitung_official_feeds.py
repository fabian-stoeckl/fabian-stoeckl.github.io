"""Negative and positive regressions for independent FIRST-PARTY RSS evidence."""
import datetime as dt
from html import escape
import unittest
import urllib.error
from unittest.mock import patch

from scripts.morgenzeitung_official_feeds import FEEDS, verify_official_feed, canonical_feed_article_link, _stamp
from scripts.morgenzeitung_live_source_check import check_candidates
from scripts.morgenzeitung_source_preflight import preflight

WHEN = "2026-10-27T08:20:00Z"
CASES = [
    ("FAZ", "https://www.faz.net/aktuell/wirtschaft/standort-article-123.html"),
    ("NZZ", "https://www.nzz.ch/wirtschaft/industrie-und-klima-ld.12345"),
    ("BBC News", "https://www.bbc.co.uk/news/articles/c1234567890o"),
    ("DIE ZEIT", "https://www.zeit.de/wirtschaft/2026-10/industrie-veraendert-sich"),
    ("DER SPIEGEL", "https://www.spiegel.de/wirtschaft/unternehmen/industrie-abc-123.html"),
    ("Handelsblatt", "https://www.handelsblatt.com/unternehmen/energie/industrie/100123456.html"),
    ("The Guardian", "https://www.theguardian.com/business/2026/oct/27/industrial-energy-news"),
    ("The New York Times", "https://www.nytimes.com/2026/10/27/business/energy-industry.html"),
    ("The Washington Post", "https://www.washingtonpost.com/business/2026/10/27/industry-climate/"),
    ("Financial Times", "https://www.ft.com/content/12345678-1234-1234-1234-123456789abc"),
    ("Süddeutsche Zeitung", "https://www.sueddeutsche.de/wirtschaft/industrie-energie-1.123456"),
]


def candidate(source, url):
    return {"id":source, "source":source, "source_url":url,
            "title":"Energiewende und die Zukunft der Industrie",
            "topic":"Industrie", "published_at":WHEN, "verified":True}


def rss(url, *, title="Energiewende und die Zukunft der Industrie",
        date="Tue, 27 Oct 2026 08:20:00 GMT", links=None):
    links = links or [url]
    return ('<?xml version="1.0"?><rss version="2.0"><channel>'
            + "".join("<item><title>"+escape(title)+"</title><link>"+escape(s)+"</link><pubDate>"
                      + escape(date)+"</pubDate></item>" for s in links)
            +"</channel></rss>").encode()


class Response:
    def __init__(self, data, status=200, content_type="application/rss+xml"):
        self.status = status
        self.data = data
        self.headers = {"Content-Type": content_type}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.data[:n]


class FakeOpener:
    def __init__(self, source, url, *, xml=None, status=403, wrong=False):
        self.source, self.url = source, url
        self.xml = xml if xml is not None else rss(url)
        self.status=status
        self.urls=[]
    def open(self, request, timeout=10):
        url=request.full_url
        self.urls.append(url)
        if url in FEEDS[self.source][0]:
            return Response(self.xml)
        if url==self.url:
            raise urllib.error.HTTPError(url,self.status,"blocked",{},None)
        raise AssertionError("Unknown request (no unapproved services): "+url)


class OfficialFeedTests(unittest.TestCase):
    def test_all_eleven_publishers_verify_official_xml_when_original_is_blocked(self):
        for label,url in CASES:
            with self.subTest(source=label):
                op=FakeOpener(label,url)
                report=check_candidates([candidate(label,url)],"2026-10-27",
                                        opener=op,publisher_dates=True)
                self.assertTrue(report["live_source_checks_passed"])
                rec=report["checked"][0]
                self.assertFalse(rec["original_article_http_verified"])
                self.assertTrue(rec["publisher_feed_verified"])
                self.assertEqual(rec["publisher_date_evidence"]["status"],"match")
                self.assertEqual(rec["content_access"],"metadata_only")
                self.assertEqual(rec["http_status"],None)
                self.assertTrue(all(x==url or x in FEEDS[label][0] for x in op.urls))
                self.assertEqual(len([x for x in op.urls if x==url]),2) # HEAD then GET

    def test_exact_original_link_required_not_another_story(self):
        label,url=CASES[1]
        alt=url.replace("ld.12345","ld.12346")
        with self.assertRaisesRegex(ValueError,"not independently confirmed"):
            verify_official_feed(candidate(label,url),
                opener=FakeOpener(label,url,xml=rss(alt)))

    def test_wrong_title_is_hard_error(self):
        label,url=CASES[2]
        with self.assertRaisesRegex(ValueError,"title contradicts"):
            verify_official_feed(candidate(label,url),
                opener=FakeOpener(label,url,xml=rss(url,title="A different article!")))

    def test_wrong_datetime_is_hard_error_even_with_correct_url_title(self):
        label,url=CASES[4]
        with self.assertRaisesRegex(ValueError,"timestamp contradicts"):
            check_candidates([candidate(label,url)],"2026-10-27",
                opener=FakeOpener(label,url,xml=rss(url,date="Tue, 27 Oct 2026 09:20:00 GMT")),
                publisher_dates=True)

    def test_no_external_proxy_or_wrong_publisher_domain(self):
        label,url=CASES[0]
        bads=["https://faz.net.evil.example/aktuell/abc",
              "https://www.nzz.ch/wirtschaft/fake",
              "http://www.faz.net/aktuell/wirtschaft/abc"]
        for target in bads:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    verify_official_feed(candidate(label,target),
                        opener=FakeOpener(label,url))

    def test_spoofed_feed_link_another_domain_not_accepted(self):
        label,url=CASES[3]
        fake=url.replace("zeit.de","zeit.de.evil.example")
        with self.assertRaisesRegex(ValueError,"not independently confirmed"):
            verify_official_feed(candidate(label,url),
                opener=FakeOpener(label,url,xml=rss(url,links=[fake])))

    def test_404_original_never_accepted_from_rss(self):
        label,url=CASES[5]
        op=FakeOpener(label,url,status=404)
        with self.assertRaisesRegex(ValueError,"404"):
            check_candidates([candidate(label,url)],"2026-10-27",
                             opener=op,publisher_dates=True)
        self.assertFalse(any(x in FEEDS[label][0] for x in op.urls))

    def test_unknown_publisher_and_untrusted_custom_feed_never_allowed(self):
        label,url=CASES[2]
        data={**candidate(label,url),"source":"Random Publisher",
              "publisher_feed_url":"https://evil.example/rss.xml"}
        with self.assertRaisesRegex(ValueError,"No approved"):
            verify_official_feed(data,opener=FakeOpener(label,url))
        data["source"]=label
        x=verify_official_feed(data,opener=FakeOpener(label,url))
        self.assertNotEqual(x["feed_url"],data["publisher_feed_url"])

    def test_bbc_only_approved_rss_tracking_params_can_be_removed(self):
        label,url=CASES[2]
        tracking=url+"?at_medium=RSS&at_campaign=rss"
        self.assertEqual(canonical_feed_article_link(tracking,label),url)
        evidence=verify_official_feed(candidate(label,url),
            opener=FakeOpener(label,url,xml=rss(tracking)))
        self.assertTrue(evidence["publisher_feed_verified"])
        for other in (url+"?article=another",url+"?auth=token",
                      "https://www.bbc.co.uk.evil.test"+url.split(".co.uk")[1]):
            with self.subTest(other=other),self.assertRaises(ValueError):
                canonical_feed_article_link(other,label)

    def test_spiegel_official_fragment_removed_but_not_other_anchor(self):
        label,url=CASES[4]
        decorated=url+"#ref=rss"
        self.assertEqual(canonical_feed_article_link(decorated,label),url)
        self.assertTrue(verify_official_feed(candidate(label,url),
            opener=FakeOpener(label,url,xml=rss(decorated)))["publisher_feed_verified"])
        with self.assertRaises(ValueError):
            canonical_feed_article_link(url+"#any-other-item",label)

    def test_zeit_rfc5322_minus_zero_is_utc_not_unknown_naive(self):
        label,url=CASES[3]
        date="Tue, 27 Oct 2026 08:20:00 -0000"
        self.assertEqual(_stamp(date).isoformat(),"2026-10-27T08:20:00+00:00")
        self.assertTrue(verify_official_feed(candidate(label,url),
            opener=FakeOpener(label,url,xml=rss(url,date=date)))["publisher_feed_verified"])
        with self.assertRaises(ValueError):
            _stamp("Tue, 27 Oct 2026 08:20:00")

    def test_oversized_or_dtd_xml_is_rejected(self):
        label,url=CASES[1]
        for xml in (b'<!DOCTYPE rss [<!ENTITY x "hacked">]><rss/>',
                    b'x'*(2*1024*1024+1),b'not XML'):
            with self.subTest(n=len(xml)),self.assertRaises(ValueError):
                verify_official_feed(candidate(label,url),
                    opener=FakeOpener(label,url,xml=xml))

    def test_rss_without_valid_timezone_or_timestamp_not_confirmed(self):
        label,url=CASES[3]
        with self.assertRaises(ValueError):
            verify_official_feed(candidate(label,url),
                opener=FakeOpener(label,url,xml=rss(url,date="not a date")))


    def test_all_publisher_aliases_resolve_exact_first_party_domain(self):
        aliases = {
            "Guardian": CASES[6], "NYT": CASES[7],
            "Washington Post": CASES[8], "FT": CASES[9],
            "SZ": CASES[10],
        }
        for alias, (_label, article_url) in aliases.items():
            with self.subTest(alias=alias):
                evidence = verify_official_feed(
                    candidate(alias, article_url),
                    opener=FakeOpener(_label, article_url))
                self.assertEqual(evidence["original_url"], article_url)
                self.assertTrue(evidence["publisher_feed_verified"])

    def test_extended_feeds_never_accept_wrong_story_identity(self):
        for label, article_url in CASES[6:]:
            with self.subTest(source=label):
                other = article_url + "-different"
                with self.assertRaisesRegex(ValueError, "not independently confirmed"):
                    verify_official_feed(candidate(label, article_url),
                        opener=FakeOpener(label, article_url, xml=rss(other)))

    def test_feed_redirects_are_never_silently_followed(self):
        label, article_url = CASES[6]
        from scripts.morgenzeitung_official_feeds import NoRedirect
        from urllib.request import Request
        handler = NoRedirect()
        request = Request(FEEDS[label][0][0])
        self.assertIsNone(handler.redirect_request(
            request, None, 302, "Found", {}, "https://evil.example/rss"))

    def test_financial_times_first_party_tracking_tag_is_narrowly_supported(self):
        label,url=CASES[9]
        original=url+"?syn-25a6b1a6=1"
        self.assertEqual(canonical_feed_article_link(original,label),url)
        self.assertTrue(verify_official_feed(candidate(label,url),
            opener=FakeOpener(label,url,xml=rss(original)))["publisher_feed_verified"])
        for other in (url+"?syn-25a6b1a6=2",url+"?syn-25a6b1a6=1&auth=1",
                      url+"?syn-25a6b1a6=",url+"?syn-gggggggg=1",
                      url+"?syn-25a6b1a6=1&syn-25a6b1a6=1",
                      url+"?article=other",url+"#rss"):
            with self.subTest(other=other),self.assertRaises(ValueError):
                canonical_feed_article_link(other,label)

    def test_source_preflight_accepts_independent_feed_identity_as_ready(self):
        # Production preflight uses check_candidates(...publisher_dates=True).
        # An OFFICIAL original feed can now prove a blocked article without text.
        pool=[]
        for i in range(15):
            label,url=CASES[i%len(CASES)]
            pool.append({**candidate(label,url),"id":str(i)})
        def checker(items,date,publisher_dates):
            return {"checked":[{"original_article_http_verified":False,
                                 "publisher_feed_verified":True,
                                 "publisher_feed_evidence":{"publisher":"BBC News"}}]}
        report=preflight(pool,"2026-10-27",checker=checker,minimum=15)
        self.assertFalse(report["preflight_passed"])
        self.assertEqual(report["blocked_count"],15)


if __name__=="__main__":
    unittest.main()
