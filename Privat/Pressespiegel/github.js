/* GitHub-backed editions; feedback is submitted by the user on GitHub. */
'use strict';
const GitHubPaper = {
  issueURL(repo, title, body) {
    if (!/^[A-Za-z0-9][A-Za-z0-9-]*\/[A-Za-z0-9_.-]+$/.test(repo || '')) throw Error('Privates Feedback-Repository noch nicht verbunden.');
    const url = new URL('https://github.com/' + repo + '/issues/new');
    url.searchParams.set('title', title);
    url.searchParams.set('body', body);
    return url.href;
  },
  ratingURL(repo, edition, article, value, reason) {
    return this.issueURL(repo, '[Morgenzeitung] ' + article.id + ': ' + value,
      'Typ: Bewertung\nAusgabe: ' + edition.date + '\nArtikel-ID: ' + article.id +
      '\nURL: ' + article.url + '\nBewertung: ' + value + '\nGrund: ' + (reason || '–') +
      '\n\nOptionales Feedback:\n');
  },
  async json(path) {
    const r = await fetch(path, {cache:'no-store'});
    if (!r.ok) throw Error('Ausgabe nicht erreichbar (' + r.status + ')');
    return r.json();
  },
  async edition(date) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw Error('Ungültiges Ausgabedatum');
    const data = await this.json('./data/' + date + '.json');
    if (data.date !== date) throw Error('Ausgabe und Datum stimmen nicht überein');
    return data;
  }
};
if (typeof module !== 'undefined') module.exports = GitHubPaper;
