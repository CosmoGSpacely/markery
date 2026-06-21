"""Shared CSS for all Markery research-site pages."""

# Palette: "Ink Wash" — charcoal #4A4A4A, light gray #CBCBCB,
# cream #FFFFE3, slate blue #6D8196.
_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: Georgia, 'Times New Roman', serif;
  background: #FFFFE3;
  color: #4A4A4A;
  line-height: 1.65;
  font-size: 16px;
}

a { color: #4F6076; text-decoration: underline; }
a:hover { color: #3a4656; }

/* ── Accessibility ── */
.skip-link {
  position: absolute;
  left: -9999px; top: 0;
  background: #4A4A4A; color: #FFFFE3;
  padding: 8px 14px; z-index: 200;
  text-decoration: none;
}
.skip-link:focus { left: 8px; top: 8px; }
:focus-visible { outline: 2px solid #6D8196; outline-offset: 2px; }

/* ── Small-screen layout ── */
@media (max-width: 640px) {
  .global-bar { padding: 8px 18px; }
  .project-bar { padding: 10px 18px; }
  .breadcrumb { padding: 8px 18px; }
  .page-header { padding: 28px 18px; }
  .page-header h1 { font-size: 1.6em; }
  .page-body { padding: 28px 18px; }
  .essay-media { grid-template-columns: 1fr; }
}

/* ── Global bar (Markery Research + site-wide search) ── */
.global-bar {
  background: #2f2f2f;
  color: #FFFFE3;
  padding: 8px 40px;
  display: flex;
  align-items: center;
  gap: 24px;
  position: sticky;
  top: 0;
  z-index: 110;
}
.global-bar .site-title {
  font-size: 1.05em;
  font-weight: normal;
  letter-spacing: .04em;
  color: #FFFFE3;
  text-decoration: none;
}
.global-bar .site-search { margin-left: auto; }

/* ── Project sub-header (project title + section nav), sticky below the bar ── */
.project-bar {
  background: #3a3a3a;
  color: #FFFFE3;
  padding: 10px 40px;
  display: flex;
  align-items: baseline;
  gap: 24px;
  position: sticky;
  top: 39px;            /* clears the global bar */
  z-index: 100;
}
.project-bar-title {
  font-size: .95em;
  font-weight: bold;
  letter-spacing: .03em;
  color: #FFFFE3;
  text-decoration: none;
  white-space: nowrap;
}
.project-nav {
  overflow-x: auto;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
  flex: 1;
  min-width: 0;
}
.project-nav a {
  color: #CBCBCB;
  text-decoration: none;
  font-size: .85em;
  margin-right: 16px;
}
.project-nav a:hover { color: #FFFFE3; }
.project-nav a.active {
  color: #FFFFE3;
  border-bottom: 2px solid #6D8196;
  padding-bottom: 3px;
}

/* ── Breadcrumb ── */
.breadcrumb {
  padding: 8px 40px;
  background: #ECECDF;
  border-bottom: 1px solid #CBCBCB;
  font-size: .78em;
}
.breadcrumb ol { list-style: none; display: flex; flex-wrap: wrap; gap: 0; margin: 0; padding: 0; }
.breadcrumb li { color: #888; }
.breadcrumb li:not(:last-child)::after { content: "›"; margin: 0 8px; color: #6D8196; }
.breadcrumb a { color: #4F6076; text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }

/* ── Page header ── */
.page-header {
  background: #4A4A4A;
  color: #FFFFE3;
  padding: 40px;
}
.page-header h1 {
  font-size: 2em;
  font-weight: normal;
  margin-bottom: 6px;
}
.page-header .subtitle {
  color: #CBCBCB;
  font-size: .95em;
}
.page-header .stat-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}
/* Inline stat labels — deliberately not pill/button-shaped (no border,
   square-ish corners) so they don't read as interactive controls. */
.chip {
  background: rgba(255,255,255,.08);
  color: #FFFFE3;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: .8em;
  font-family: monospace;
}

/* ── Page body ── */
.page-body { max-width: 960px; margin: 0 auto; padding: 48px 40px; }

.narrative {
  max-width: 700px;
  margin-bottom: 40px;
}
.narrative h2 {
  font-size: 1.2em;
  font-weight: normal;
  margin: 32px 0 10px;
  color: #4A4A4A;
}
.narrative p { margin-bottom: 1em; }
.narrative table {
  width: 100%;
  border-collapse: collapse;
  font-size: .88em;
  margin: 16px 0;
}
.narrative th, .narrative td {
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid #CBCBCB;
}
.narrative th { background: #ECECDF; font-weight: normal; color: #555; }
.narrative code {
  font-family: monospace;
  font-size: .88em;
  background: #ECECDF;
  padding: 1px 4px;
  border-radius: 2px;
}
.narrative pre {
  background: #ECECDF;
  padding: 14px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: .83em;
}

/* ── Timeline ── */
.timeline-section { margin-bottom: 40px; }
.timeline-section h2 {
  font-size: 1em;
  font-weight: normal;
  color: #555;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 12px;
}
.timeline-svg { width: 100%; overflow: visible; }

/* ── Vertical scroll timeline (left rail + chronological card column) ── */
.timeline-layout { position: relative; margin-bottom: 48px; }
.timeline-layout::before {
  content: "";
  position: absolute;
  top: 8px; bottom: 8px; left: 74px;
  width: 2px;
  background: #CBCBCB;
}
.tl-row {
  display: grid;
  grid-template-columns: 74px 1fr;
  gap: 28px;
  margin-bottom: 28px;
}
/* The year marker sticks to the top of the viewport while its cards scroll past,
   so it reads as a moving point on the rail — time advancing as you scroll. */
.tl-year {
  position: sticky;
  top: 92px;
  align-self: start;
  text-align: right;
  padding-right: 18px;     /* keep the number clear of the dot on the rail */
  line-height: 1.3;
  font-family: monospace;
  font-weight: bold;
  font-size: 1em;
  color: #4A4A4A;
}
.tl-year::after {
  content: "";
  position: absolute;
  right: -7px; top: 4px;
  width: 11px; height: 11px;
  border-radius: 50%;
  background: #6D8196;
  border: 2px solid #FFFFE3;
}
.tl-year--undated { color: #999; font-weight: normal; font-size: .85em; }
.tl-year--undated::after { background: #CBCBCB; }
.tl-cards { min-width: 0; }
.tl-cards.card-grid { margin-bottom: 0; }
@media (max-width: 560px) {
  .timeline-layout::before { left: 58px; }
  .tl-row { grid-template-columns: 58px 1fr; gap: 16px; }
  .tl-year { font-size: .85em; padding-right: 12px; }
}

/* ── Card grid ── */
.section-title {
  font-size: 1em;
  font-weight: normal;
  color: #555;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 16px;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.card--focus {
  border: 2px solid #6D8196;
  box-shadow: 0 2px 8px rgba(109,129,150,.25);
}
.focus-badge {
  display: inline-block;
  background: #6D8196;
  color: #FFFFE3;
  font-size: .65em;
  padding: 1px 6px;
  border-radius: 10px;
  margin-top: 2px;
  font-family: monospace;
}
.research-question {
  background: #ECECDF;
  border-left: 4px solid #6D8196;
  padding: 16px 20px;
  margin-bottom: 32px;
  max-width: 700px;
}
.research-question .rq-label {
  display: block;
  font-size: .72em;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #4F6076;
  margin-bottom: 8px;
}
.research-question p { margin-bottom: .7em; }
.research-question p:last-child { margin-bottom: 0; }
.card-image {
  width: 100%;
  height: 140px;
  object-fit: contain;
  background: #FBFBF0;
  border-bottom: 1px solid #eee;
  display: block;
}
.card-image-placeholder {
  width: 100%;
  height: 140px;
  background: #ECECDF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: .75em;
  font-family: monospace;
  border-bottom: 1px solid #eee;
}
.card-body { padding: 10px 12px; flex: 1; display: flex; flex-direction: column; gap: 4px; }
.card-name { font-weight: bold; font-size: .88em; line-height: 1.3; }
.card-meta { font-size: .75em; color: #666; }
.card-goods { font-size: .73em; color: #444; margin-top: 4px; line-height: 1.4;
  border-top: 1px solid #eee; padding-top: 4px; }
.card-footer { font-size: .7em; color: #999; font-family: monospace; margin-top: auto; padding-top: 4px; }
.entity-badge {
  display: inline-block;
  background: #CBCBCB;
  color: #4A4A4A;
  font-size: .68em;
  padding: 1px 6px;
  border-radius: 10px;
  margin-top: 2px;
  font-family: monospace;
}
a.entity-badge { text-decoration: none; }
a.entity-badge:hover { background: #6D8196; color: #FFFFE3; }

/* Empty-state copy when a section has no records. */
.empty-state {
  color: #777;
  font-style: italic;
  padding: 20px 0;
}
.match-link {
  display: inline-block;
  background: #6D8196;
  color: #FFFFE3;
  font-size: .8em;
  font-weight: bold;
  padding: 5px 12px;
  border-radius: 4px;
  text-decoration: none;
  margin-top: 8px;
  letter-spacing: .02em;
}
.match-link:hover { background: #56697d; color: #FFFFE3; }
.match-link--lg { font-size: .95em; padding: 9px 18px; margin-top: 14px; }

/* Card image and title link to the per-record detail page (SITE-REVIEW #11). */
.card-image-link { display: block; }
.card-name a { color: inherit; text-decoration: none; }
.card-name a:hover { color: #4F6076; text-decoration: underline; }

/* ── Entity grid ── */
.entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.entity-card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  padding: 20px;
}
.entity-card h3 { font-size: 1.1em; font-weight: normal; margin-bottom: 8px; }
.entity-card .entity-meta { font-size: .8em; color: #666; margin-bottom: 12px; }
.entity-card .entity-stats {
  display: flex;
  gap: 16px;
  font-size: .78em;
  color: #444;
  margin-bottom: 12px;
}
.entity-card .stat-val { font-weight: bold; color: #4A4A4A; }
.entity-card .links a { font-size: .82em; margin-right: 12px; }

/* ── Match cards (landing page) ── */
.match-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.match-card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  display: flex;
  gap: 16px;
  padding: 16px;
}
.match-card-thumb {
  width: 80px;
  min-width: 80px;
  height: 80px;
  object-fit: contain;
  background: #FBFBF0;
  border: 1px solid #eee;
  border-radius: 3px;
}
.match-card-thumb-placeholder {
  width: 80px;
  min-width: 80px;
  height: 80px;
  background: #ECECDF;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: .7em;
}
.match-card-body { flex: 1; }
.match-card-title { font-weight: bold; font-size: .95em; margin-bottom: 4px; }
.match-card-meta { font-size: .78em; color: #666; margin-bottom: 8px; }
.match-card-note { font-size: .8em; color: #444; line-height: 1.4; margin-bottom: 8px; }

/* ── Essay page ── */
.essay { max-width: 700px; }
.essay h2 { font-size: 1.2em; font-weight: normal; margin: 36px 0 10px; color: #4A4A4A; }
.essay p { margin-bottom: 1em; }
.essay table { width: 100%; border-collapse: collapse; font-size: .88em; margin: 16px 0; }
.essay th, .essay td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #CBCBCB; }
.essay th { background: #ECECDF; font-weight: normal; color: #555; }
.essay pre { background: #ECECDF; padding: 14px; overflow-x: auto; margin: 12px 0; font-size: .83em; }
.essay code { font-family: monospace; font-size: .88em; background: #ECECDF; padding: 1px 4px; border-radius: 2px; }
.essay-media {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 24px 0;
}
.essay-media img {
  width: 100%;
  object-fit: contain;
  border: 1px solid #CBCBCB;
  background: #FBFBF0;
}
.essay-media .media-label { font-size: .75em; color: #888; margin-top: 4px; text-align: center; }
.sources {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #CBCBCB;
  font-size: .82em;
  color: #555;
}
.sources h2 { font-size: .95em; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 12px; }
.sources dt { font-weight: bold; margin-top: 8px; }
.sources dd { margin-left: 16px; }

/* ── Timeline annotation page ── */
.timeline-entries { max-width: 700px; margin-top: 40px; }
.timeline-entries h3 {
  font-size: 1.05em;
  font-weight: bold;
  color: #4A4A4A;
  margin: 32px 0 6px;
  border-left: 3px solid #6D8196;
  padding-left: 10px;
}
.timeline-entries p { margin-bottom: .8em; }

/* ── Thematic essay ── */
.theme-essay { max-width: 700px; }
.theme-essay h2 { font-size: 1.2em; font-weight: normal; margin: 32px 0 10px; color: #4A4A4A; }
.theme-essay h3 { font-size: 1.05em; font-weight: normal; margin: 24px 0 8px; color: #6D8196; }
.theme-essay p { margin-bottom: 1em; }
.theme-essay table { width: 100%; border-collapse: collapse; font-size: .88em; margin: 16px 0; }
.theme-essay th, .theme-essay td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #CBCBCB; }
.theme-essay th { background: #ECECDF; font-weight: normal; color: #555; }

/* ── Search page ── */
.search-form { display: flex; gap: 8px; margin-bottom: 32px; }
.search-form input[type=search] {
  flex: 1; padding: 8px 12px; border: 1px solid #CBCBCB; border-radius: 3px;
  font-size: 1em; font-family: Georgia, serif; background: #fff;
}
.search-form button {
  padding: 8px 18px; background: #6D8196; color: #FFFFE3;
  border: none; border-radius: 3px; cursor: pointer; font-size: .9em;
}
.search-results { list-style: none; }
.search-results li { margin-bottom: 20px; }
.search-results .result-title { font-size: 1.05em; font-weight: bold; }
.search-results .result-type { font-size: .75em; color: #888; font-family: monospace; margin-left: 6px; }
.search-results .result-excerpt { font-size: .88em; color: #444; margin-top: 4px; }

/* ── Search input in header ── */
.site-search { margin-left: auto; }
.site-search input[type=search] {
  padding: 3px 8px; border: 1px solid #6D8196; border-radius: 3px;
  background: #2f2f2f; color: #FFFFE3; font-size: .8em; width: 140px;
}
.site-search input[type=search]::placeholder { color: #CBCBCB; }

/* ── Patent figure (embedded via [[figure:patent_no]]) ── */
.patent-figure { margin: 24px auto; text-align: center; max-width: 600px; border: 1px solid #CBCBCB; border-radius: 4px; padding: 8px; }
.patent-figure img { max-width: 100%; background: #FBFBF0; display: block; margin: 0 auto; }
.patent-figure figcaption { font-size: .78em; color: #888; margin-top: 6px; font-style: italic; font-family: Georgia, 'Times New Roman', serif; }

/* ── Blockquotes ── */
blockquote { border-left: 3px solid #6D8196; margin: 16px 0; padding: 8px 16px; color: #555; font-style: italic; }
blockquote p { margin: 0; }

/* ── Small chip (inline stat tags) ── */
.chip-sm { font-size: .75em; background: #CBCBCB; border-radius: 3px; padding: 1px 6px; color: #4A4A4A; white-space: nowrap; }

/* ── Root portal (Markery landing across all projects) ── */
.portal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 48px;
}
.portal-card {
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0,0,0,.1);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.portal-title { font-size: 1.2em; font-weight: normal; }
.portal-title a { color: #4A4A4A; text-decoration: none; }
.portal-title a:hover { color: #4F6076; text-decoration: underline; }
.portal-thumbs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.portal-thumb {
  width: 100%;
  height: 120px;
  object-fit: contain;
  background: #FBFBF0;
  border: 1px solid #CBCBCB;
  border-radius: 4px;
}
.portal-thumb--ph {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 10px;
  background: #ECECDF;
  color: #777;
  font-size: .8em;
  font-weight: bold;
}
.portal-summary { font-size: .9em; color: #444; line-height: 1.5; flex: 1; }
.portal-stats { display: flex; flex-wrap: wrap; gap: 6px; }
.portal-enter {
  align-self: flex-start;
  background: #6D8196;
  color: #FFFFE3;
  font-size: .85em;
  font-weight: bold;
  padding: 6px 14px;
  border-radius: 4px;
  text-decoration: none;
}
.portal-enter:hover { background: #56697d; color: #FFFFE3; }

/* ── Per-record detail page (one trademark / one patent) ── */
.detail-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 32px;
  align-items: start;
}
.detail-media { position: sticky; top: 92px; }
.detail-image {
  width: 100%;
  object-fit: contain;
  background: #FBFBF0;
  border: 1px solid #CBCBCB;
  border-radius: 4px;
  display: block;
}
.detail-image-placeholder {
  width: 100%;
  min-height: 220px;
  background: #ECECDF;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  color: #777;
  font-weight: bold;
}
.detail-media .match-link { display: block; text-align: center; }
.detail-fields {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 8px 20px;
  font-size: .92em;
}
.detail-fields dt { font-weight: bold; color: #555; }
.detail-fields dd { margin: 0; }
@media (max-width: 640px) {
  .detail-layout { grid-template-columns: 1fr; }
  .detail-media { position: static; }
}

/* ── Site footer ── */
.site-footer {
  margin-top: 48px; padding: 20px 24px; border-top: 1px solid #CBCBCB;
  font-size: .78em; color: #888; text-align: center;
}
.site-footer a { color: #6D8196; text-decoration: none; }
.site-footer a:hover { text-decoration: underline; }
"""
