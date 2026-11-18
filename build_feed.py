#!/usr/bin/env python3
"""Daily, short-lived RSS snapshot of a user's attended setlists via setlist.fm API."""
import datetime as dt
import email.utils
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER = os.getenv('SETLIST_USER', 'carlosubeda')
API_KEY = os.getenv('SETLIST_API_KEY', '')
BASE_URL = os.getenv('FEED_BASE_URL', '').rstrip('/')
OUT_DIR = pathlib.Path(os.getenv('OUTPUT_DIR', 'public'))
SOURCE = f'https://www.setlist.fm/attended/{urllib.parse.quote(USER)}'


def retrieve(page):
    url = f'https://api.setlist.fm/rest/1.0/user/{urllib.parse.quote(USER)}/attended?p={page}'
    req = urllib.request.Request(url, headers={
        'x-api-key': API_KEY, 'Accept': 'application/json',
        'Accept-Language': 'es', 'User-Agent': 'personal-attended-rss/1.0',
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def fetch_all():
    result = []
    page = 1
    while True:
        payload = retrieve(page)
        rows = payload.get('setlist') or []
        result.extend(rows)
        total = int(payload.get('total') or 0)
        per_page = int(payload.get('itemsPerPage') or len(rows) or 20)
        if not rows or (total and len(result) >= total) or len(rows) < per_page:
            break
        page += 1
        if page > 200:
            raise RuntimeError('Unexpected pagination: >200 pages')
        time.sleep(0.3)
    if not result:
        raise RuntimeError('No attended setlists returned; refusing to publish an empty feed')
    # stable deduplication
    return list({str(row.get('id') or row.get('url')): row for row in result}.values())


def utc_date(date_str):
    return dt.datetime.strptime(date_str, '%d-%m-%Y').replace(tzinfo=dt.timezone.utc)



def build(rows):
    now = dt.datetime.now(dt.timezone.utc)
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    root = ET.Element('rss', version='2.0')
    channel = ET.SubElement(root, 'channel')
    for name, value in [
        ('title', f'Conciertos a los que ha asistido {USER} | setlist.fm'),
        ('link', SOURCE),
        ('description', 'Conciertos marcados como asistidos en setlist.fm. Fuente: setlist.fm.'),
        ('language', 'es-es'),
        ('lastBuildDate', email.utils.format_datetime(now, usegmt=True)),
        ('ttl', '1440'),
    ]:
        ET.SubElement(channel, name).text = value
    ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link', {
        'href': f'{BASE_URL}/rss.xml', 'rel': 'self', 'type': 'application/rss+xml',
    })
    def sort_key(row):
        try:
            return utc_date(row.get('eventDate', '01-01-1900'))
        except ValueError:
            return dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc)
    for row in sorted(rows, key=sort_key, reverse=True):
        artist = (row.get('artist') or {}).get('name') or 'Artista desconocido'
        venue = row.get('venue') or {}
        city = (venue.get('city') or {}).get('name') or ''
        place = ', '.join(x for x in [venue.get('name', ''), city] if x)
        date = row.get('eventDate', '')
        link = row.get('url') or SOURCE
        item = ET.SubElement(channel, 'item')
        for name, value in [('title', f'{artist} — {place} ({date})'), ('link', link),
                            ('description', f'{artist}. {place}. Fecha del concierto: {date}. Fuente: setlist.fm.')]:
            ET.SubElement(item, name).text = value
        ET.SubElement(item, 'guid', isPermaLink='true' if row.get('url') else 'false').text = link if row.get('url') else str(row.get('id', ''))
        try:
            ET.SubElement(item, 'pubDate').text = email.utils.format_datetime(utc_date(date), usegmt=True)
        except ValueError:
            pass
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def main():
    if not API_KEY:
        sys.exit('Missing SETLIST_API_KEY (setlist.fm API key)')
    if not BASE_URL.startswith('https://'):
        sys.exit('Missing valid FEED_BASE_URL (https://... excluding trailing slash)')
    rows = fetch_all()
    xml = build(rows)
    ET.fromstring(xml)  # validation
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'rss.xml').write_bytes(xml)
    (OUT_DIR / '.nojekyll').touch()
    (OUT_DIR / 'index.html').write_text(
        '<!doctype html><html lang="es"><meta charset="utf-8"><title>RSS setlist.fm</title>'
        f'<h1>Conciertos de {USER}</h1><p><a href="rss.xml">Suscribirse al RSS</a></p>'
        f'<p>Fuente: <a href="{SOURCE}">setlist.fm</a></p></html>', encoding='utf-8')
    print(f'RSS generated with {len(rows)} concerts at {OUT_DIR / "rss.xml"}')


if __name__ == '__main__':
    main()
