"""No-network regression tests for Noahpinion feed extraction."""
import unittest
from scripts.sync_blogs import parse_feed, excerpt, merge_archive, article_summary_valid


def entry(title, author, date, slug):
    return (f"<item><title>{title}</title><link>https://www.noahpinion.blog/p/{slug}</link>"
            f"<dc:creator>{author}</dc:creator><pubDate>{date}</pubDate>"
            "<description><![CDATA[<p>Short <b>text</b> &amp; more.</p>]]></description></item>")


class BlogFeedTests(unittest.TestCase):
    def test_all_available_posts_including_guests(self):
        dates = ["Mon, 02 Nov 2026 10:00:00 +0000", "Sat, 31 Oct 2026 10:00:00 +0000",
                 "Thu, 29 Oct 2026 10:00:00 +0000", "Tue, 27 Oct 2026 10:00:00 +0000",
                 "Sun, 25 Oct 2026 10:00:00 +0000"]
        items = [entry("Guest", "Ramez Naam", "Tue, 03 Nov 2026 10:00:00 +0000", "guest")]
        items += [entry("Noah " + str(i), "Noah Smith", date, "post-" + str(i))
                  for i, date in enumerate(dates)]
        xml = ('<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
               + "".join(reversed(items)) + "</channel></rss>").encode()
        posts = parse_feed(xml)["posts"]
        self.assertEqual([p["title"] for p in posts],
                         ["Guest", "Noah 0", "Noah 1", "Noah 2", "Noah 3", "Noah 4"])
        self.assertEqual(posts[0]["author"], "Ramez Naam")
        self.assertEqual(posts[0]["description"], "Short text & more.")

    def test_keeps_old_data_on_insufficient_unique_posts(self):
        items = [entry("Safe", "Noah Smith", "Mon, 02 Nov 2026 10:00:00 +0000", "same")
                 for _ in range(5)]
        items.append('<item><title>Attack</title><link>https://attacker.example/</link></item>')
        with self.assertRaises(ValueError):
            parse_feed(('<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
                        + "".join(items) + "</channel></rss>").encode())

    def test_archives_old_entries_outside_current_feed(self):
        dates = ["Mon, 02 Nov 2026 10:00:00 +0000", "Sat, 31 Oct 2026 10:00:00 +0000",
                 "Thu, 29 Oct 2026 10:00:00 +0000", "Tue, 27 Oct 2026 10:00:00 +0000",
                 "Sun, 25 Oct 2026 10:00:00 +0000"]
        items = [entry("Recent " + str(i), "Noah Smith", date, "recent-" + str(i))
                 for i, date in enumerate(dates)]
        xml = ('<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
               + "".join(items) + "</channel></rss>").encode()
        fresh = parse_feed(xml)
        old = {
            "posts": [
                fresh["posts"][0],
                {"title": "Older post", "url": "https://www.noahpinion.blog/p/older",
                 "published_at": "2026-10-15", "description": "Historical item"},
                {"title": "Invalid post", "url": "https://evil.example/invalid",
                 "published_at": "2026-10-01"}
            ]
        }
        merged = merge_archive(fresh, old)
        self.assertEqual(len(merged["posts"]), 6)
        self.assertEqual(merged["posts"][-1]["title"], "Older post")
        self.assertEqual(merged["posts"][0]["title"], "Recent 0")


    def test_source_summary_survives_refresh_and_archive(self):
        dates = ["Mon, 02 Nov 2026 10:00:00 +0000", "Sat, 31 Oct 2026 10:00:00 +0000",
                 "Thu, 29 Oct 2026 10:00:00 +0000", "Tue, 27 Oct 2026 10:00:00 +0000",
                 "Sun, 25 Oct 2026 10:00:00 +0000"]
        items = [entry("Recent " + str(i), "Noah Smith", date, "recent-" + str(i))
                 for i, date in enumerate(dates)]
        xml = ('<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
               + "".join(items) + "</channel></rss>").encode()
        fresh = parse_feed(xml)
        original = dict(fresh["posts"][0])
        summary = " ".join(["Grounded editorial insight about economics and technology."] * 20)
        original.update(summary_text=summary, summary_source="article",
                        summary_language="en", summary_access="visible_text_only",
                        summary_generated_at="2026-11-06T11:00:00+01:00",
                        summary_evidence_url=original["url"])
        self.assertTrue(article_summary_valid(original))
        previous = {"posts": [original, {
            "title": "Historic post", "url": "https://www.noahpinion.blog/p/historic",
            "published_at": "2026-10-01", "description": "Old RSS teaser",
            **{f: original[f] for f in ("summary_text", "summary_source",
              "summary_language", "summary_access", "summary_generated_at")}
        }]}
        merged = merge_archive(fresh, previous)
        self.assertEqual(len(merged["posts"]), 6)
        self.assertEqual(merged["posts"][0]["summary_text"], summary)
        self.assertEqual(merged["posts"][-1]["summary_text"], summary)
        self.assertEqual(merged["posts"][0]["description"], "Short text & more.")
        self.assertEqual(merged["posts"][0]["summary_evidence_url"], original["url"])
        second = merge_archive(parse_feed(xml), merged)
        self.assertEqual(len(second["posts"]), 6)
        self.assertEqual(second["posts"][0]["summary_text"], summary)

    def test_summary_provenance_and_length_restrictions(self):
        sample = {"url": "https://www.noahpinion.blog/p/example",
                  "summary_text": " ".join(["One"] * 115),
                  "summary_source": "article", "summary_language": "en",
                  "summary_access": "visible_text_only",
                  "summary_evidence_url": "https://www.noahpinion.blog/p/example",
                  "summary_generated_at": "2026-11-06T11:00:00+01:00"}
        self.assertTrue(article_summary_valid(sample))
        for changes in (
            {"summary_text": "Short RSS blurb."},
            {"summary_text": " ".join(["Long"] * 151)},
            {"summary_source": "rss"},
            {"summary_language": "fr"},
            {"summary_generated_at": "not-a-timestamp"},
            {"summary_evidence_url": "https://evil.example/p/example"},
        ):
            self.assertFalse(article_summary_valid({**sample, **changes}))

    def test_html_stripping(self):
        self.assertEqual(excerpt("<p>One <em>two</em></p>"), "One two")


if __name__ == "__main__":
    unittest.main()
