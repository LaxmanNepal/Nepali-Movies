import json, html, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'movies.json'
OUT = ROOT / 'movies'
BASE = 'https://apps.laxmannepal.com.np/Nepali-Movies'

def slug(text):
    text = re.sub(r'[^\w\s-]', '', str(text), flags=re.UNICODE).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text[:90] or 'movie'

def esc(v):
    return html.escape(str(v or ''), quote=True)

def unique_slug(title, mid, used):
    base = slug(title)
    candidate = base
    if candidate in used:
        candidate = f'{base}-{slug(mid)[:10]}'
    used.add(candidate)
    return candidate

catalog = json.loads(DATA.read_text(encoding='utf-8'))
movies = catalog.get('movies', [])
OUT.mkdir(exist_ok=True)
used = set()
entries = []
for m in movies:
    mid = m.get('id') or m.get('youtubeVideoId')
    if not mid:
        continue
    s = unique_slug(m.get('title', 'Nepali Movie'), mid, used)
    title = m.get('title', 'Nepali Movie')
    creator = (m.get('creator') or {}).get('name', 'YouTube Creator')
    year = m.get('year') or ''
    genres = m.get('genre') or ['Nepali Cinema']
    desc = (m.get('description') or f'Watch {title} and discover more Nepali cinema from its YouTube source.')[:300]
    thumb = m.get('thumbnail') or ''
    url = f'{BASE}/movies/{s}/'
    payload = json.dumps(m, ensure_ascii=False).replace('</script>', '<\\/script>')
    related = [x for x in movies if x.get('id') != mid][:8]
    cards = ''.join(f'''<a class="card" href="../{unique_slug(x.get('title','movie'), x.get('id',''), set())}/"><img src="{esc(x.get('thumbnail',''))}" alt="{esc(x.get('title','Nepali Movie'))}" loading="lazy"><strong>{esc(x.get('title','Nepali Movie'))}</strong><small>{esc(x.get('year',''))} · {esc((x.get('genre') or ['Cinema'])[0])}</small></a>''' for x in related)
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#08090c"><title>{esc(title)} — Nepali Movies</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(url)}"><meta property="og:type" content="video.movie"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{esc(thumb)}"><meta property="og:url" content="{esc(url)}"><link rel="stylesheet" href="../../styles.css"><style>.detail{{max-width:1100px;margin:auto;padding:22px 16px 100px}}.back{{display:inline-flex;padding:10px 14px;border-radius:12px;background:#181a20;color:#fff;text-decoration:none;margin-bottom:16px}}.video{{position:relative;aspect-ratio:16/9;background:#000;border-radius:18px;overflow:hidden;box-shadow:0 20px 60px #0008}}.video iframe{{width:100%;height:100%;border:0}}.meta{{padding:20px 0}}.meta h1{{font-size:clamp(28px,6vw,48px);margin:0 0 10px}}.chips{{display:flex;gap:8px;flex-wrap:wrap}.chip{{padding:7px 11px;background:#1c1e25;border-radius:999px;color:#bbb}}.source{{margin-top:18px;padding:16px;background:#14161b;border-radius:16px}}.source a{{color:#fff}}.related-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}}.card{{color:#fff;text-decoration:none}}.card img{{width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:12px;background:#181a20}}.card strong,.card small{{display:block;margin-top:7px}}.card small{{color:#8f949f}}@media(max-width:600px){{.detail{{padding:12px 12px 90px}}.video{{border-radius:12px}}}}</style><script type="application/ld+json">{json.dumps({'@context':'https://schema.org','@type':'Movie','name':title,'description':desc,'image':thumb,'dateCreated':str(year) if year else None,'url':url,'sameAs':m.get('youtubeUrl')},ensure_ascii=False).replace('None','null')}</script></head><body><main class="detail"><a class="back" href="../../">← Nepali Movies</a><div class="video"><iframe src="https://www.youtube.com/embed/{esc(m.get('youtubeVideoId',''))}?rel=0&playsinline=1" title="{esc(title)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><section class="meta"><h1>{esc(title)}</h1><div class="chips"><span class="chip">{esc(year)}</span><span class="chip">{esc(' · '.join(genres))}</span></div><p>{esc(desc)}</p><div class="source"><strong>Original YouTube source</strong><br><a href="{esc(m.get('youtubeUrl',''))}" target="_blank" rel="noopener">{esc(creator)}</a></div></section><section><h2>More Nepali Movies</h2><div class="related-grid">{cards}</div></section></main></body></html>'''
    path = OUT / s / 'index.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding='utf-8')
    entries.append((url, title))

sitemap = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',f'<url><loc>{BASE}/</loc></url>']
for url, _ in entries:
    sitemap.append(f'<url><loc>{esc(url)}</loc></url>')
sitemap.append('</urlset>')
(ROOT / 'sitemap.xml').write_text('\n'.join(sitemap), encoding='utf-8')
(ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n', encoding='utf-8')
print(f'Generated {len(entries)} movie pages and sitemap.')
