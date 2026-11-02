"""No-network regression tests for Noahpinion feed extraction."""
import unittest
from scripts.sync_blogs import parse_feed, excerpt


def entry(title, author, date, slug):
    return (f"<item><title>{title}</title><link>https://www.noahpinion.blog/p/{slug}</link>"
            f"<dc:creator>{author}</dc:creator><pubDate>{date}</pubDate>"
            "<description><![CDATA[<p>Short <b>text</b> &amp; more.</p>]]></description></item>")


class BlogFeedTests(unittest.TestCase):
    def test_five_newest_including_guests(self):
        dates = ["Mon, 02 Nov 2026 10:00:00 +0000", "Sat, 31 Oct 2026 10:00:00 +0000",
                 "Thu, 29 Oct 2026 10:00:00 +0000", "Tue, 27 Oct 2026 10:00:00 +0000",
                 "Sun, 25 Oct 2026 10:00:00 +0000"]
        items = [entry("Guest", "Ramez Naam", "Tue, 03 Nov 2026 10:00:00 +0000", "guest")]
        items += [entry("Noah " + str(i), "Noah Smith", date, "post-" + str(i))
                  for i, date in enumerate(dates)]
        xml = ('<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
               + "".join(reversed(items)) + "</channel></rss>").encode()
        posts = parse_feed(xml)["posts"]
        self.assertEqual([p["title"] for p in posts], ["Guest", "Noah 0", "Noah 1", "Noah 2", "Noah 3"])
        self.assertEqual(posts[0]["author"], "Ramez Naam")
        self.assertEqual(posts[0]["description"], "Short text & more.")

    def test_keeps_old_data_on_insufficient_unique_posts(self):
        items = [entry("Safe", "Noah Smith", "Mon, 02 Nov 2026 10:00:00 +0000", "same")
                 for _ in range(5)]
        items.append('<item><title>Attack</title><link>https://attacker.example/</link></item>')
        with self.assertRaises(ValueError):
            parse_feed(('<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
                        + "".join(items) + "</channel></rss>").encode())

    def test_html_stripping(self):
        self.assertEqual(excerpt("<p>One <em>two</em></p>"), "One two")


if __name__ == "__main__":
    unittest.main()
