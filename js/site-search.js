/* Search the current static index without external search dependencies. */
(() => {
  "use strict";
  const input = document.getElementById("search-query");
  const results = document.getElementById("search-hits");
  if (!input || !results) return;
  results.setAttribute("aria-live", "polite");
  let records;
  let timer;
  const normalize = value => String(value || "").toLocaleLowerCase().trim();
  const index = () => records || (records = fetch("/index.json", {cache: "no-store"})
    .then(response => {
      if (!response.ok) throw new Error("Search unavailable");
      return response.json();
    }).catch(error => { records = undefined; throw error; }));

  const show = async () => {
    const query = input.value.trim();
    results.replaceChildren();
    const url = new URL(window.location.href);
    if (query) url.searchParams.set("q", query);
    else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    if (!query) return;
    const terms = normalize(query).split(/\s+/);
    try {
      const all = await index();
      if (input.value.trim() !== query) return;
      const matches = all.map(record => {
        const title = normalize(record.title);
        const text = normalize([record.title, record.summary, record.content,
          ...(record.authors || []), ...(record.tags || [])].join(" "));
        return {record, match: terms.every(term => text.includes(term)),
          score: terms.reduce((score, term) => score + (title.includes(term) ? 1 : 0), 0)};
      }).filter(item => item.match).sort((a, b) => b.score - a.score);
      results.replaceChildren();
      const heading = document.createElement("h3");
      heading.textContent = matches.length ? `${matches.length} results found` : "No results found";
      results.append(heading);
      for (const {record} of matches) {
        const article = document.createElement("article");
        article.className = "search-hit";
        const title = document.createElement("div");
        title.className = "search-hit-name";
        const link = document.createElement("a");
        link.href = record.relpermalink;
        link.textContent = record.title;
        title.append(link);
        const summary = document.createElement("p");
        summary.className = "search-hit-description";
        summary.textContent = record.summary;
        article.append(title, summary);
        results.append(article);
      }
    } catch (_) {
      if (input.value.trim() === query) results.textContent = "Search could not load. Please try again.";
    }
  };

  input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(show, 120); });
  input.addEventListener("keydown", event => {
    if (event.key === "Enter") { event.preventDefault(); clearTimeout(timer); show(); }
  });
  const initial = new URL(window.location.href).searchParams.get("q");
  if (initial) {
    input.value = initial;
    document.body.classList.add("searching");
    show();
  }
})();
