// Einmal die echten, privaten Chat-Adressen eintragen. Keine Freigabe-Links verwenden.
const bereichChats = Object.freeze({
  etf: null,
  pressespiegel: null
});
for (const [topic, address] of Object.entries(bereichChats)) {
  if (!address) continue;
  let url;
  try { url = new URL(address); } catch { continue; }
  if (url.origin !== 'https://chatgpt.com' || !/^\/c\/[a-zA-Z0-9-]+$/.test(url.pathname)) continue;
  const button = document.querySelector(`[data-topic="${topic}"]`);
  if (!button) continue;
  const link = document.createElement('a');
  link.className = button.className;
  link.href = url.href;
  link.textContent = button.textContent;
  link.setAttribute('aria-label', `${topic === 'etf' ? 'ETF' : 'Pressespiegel'}: festen Änderungs-Chat öffnen`);
  button.replaceWith(link);
  document.getElementById(`${topic}-chat-status`)?.remove();
}
