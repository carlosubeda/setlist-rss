#!/usr/bin/env python3
"""Daily, short-lived RSS snapshot of a user's attended setlists by scraping the public setlist.fm attended pages."""
import datetime as dt
import email.utils
import html
import re
import os
import pathlib
import sys
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

USER = os.getenv('SETLIST_USER', 'carlosubeda')
BASE_URL = os.getenv('FEED_BASE_URL', '').rstrip('/')
OUT_DIR = pathlib.Path(os.getenv('OUTPUT_DIR', 'public'))
SOURCE = f'https://www.setlist.fm/attended/{urllib.parse.quote(USER)}'


def fetch_all():
    # Wicket pagination links depend on cookies and on the current page version.
    session = requests.Session()
    session.headers.update({'User-Agent': 'personal-attended-rss/2.0',
                            'Accept-Language': 'en-US,en;q=0.9',
'Accept-Encoding': 'identity'})
    url = SOURCE
    result = {}
    expected = None
    seen_pages = set()
    months = {m.lower(): i for i, m in enumerate(
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    for page in range(200):
        response = session.get(url, timeout=45)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        if expected is None:
            for h in soup.find_all('h2'):
                match = re.search(r'Attended Shows\s*\(\s*([\d,]+)\s*\)', h.get_text(' ', strip=True))
                if match:
                    expected = int(match.group(1).replace(',', ''))
                    break
            if expected is None or expected == 0:
                raise RuntimeError('Attendance count missing or empty; refusing to publish')
        entries = soup.select('li.setlist')
        if not entries:
            raise RuntimeError('No concerts found; possible blocking or HTML change')
        page_ids = []
        for entry in entries:
            anchor = entry.select_one('.content a[href*="setlist/"]')
            date = entry.select_one('.smallDateBlock')
            place = entry.select_one('.subline')
            if anchor is None or date is None or place is None:
                raise RuntimeError('Incomplete concert markup; refusing partial feed')
            parts = date.get_text(' ', strip=True).split()
            if len(parts) != 3:
                raise RuntimeError('Unexpected concert date')
            month, day, year = parts
            event_date = dt.date(int(year), months[month.lower()[:3]], int(day))
            link = urllib.parse.urljoin(response.url, anchor['href'])
            if urllib.parse.urlsplit(link).netloc != 'www.setlist.fm':
                raise RuntimeError('Unexpected concert host')
            page_ids.append(link)
            result[link] = {'url': link, 'artist': {'name': anchor.get_text(' ', strip=True)},
                            'venue': {'name': place.get_text(' ', strip=True)},
                            'eventDate': event_date.strftime('%d-%m-%Y')}
        signature = tuple(page_ids)
        if signature in seen_pages:
            raise RuntimeError('Pagination repeated a page; refusing partial feed')
        seen_pages.add(signature)
        next_link = soup.find('a', title='Go to next page')
        if next_link is None:
            if len(result) != expected:
                raise RuntimeError(f'Expected {expected} concerts, received {len(result)}')
            return list(result.values())
        url = urllib.parse.urljoin(response.url, next_link['href'])
        if urllib.parse.urlsplit(url).netloc != 'www.setlist.fm':
            raise RuntimeError('Unexpected pagination host')
        time.sleep(2)
    raise RuntimeError('Unexpected pagination: more than 200 pages')


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
        f'<h1>Conciertos de {html.escape(USER)}</h1><p><a href="rss.xml">Suscribirse al RSS</a></p>'
        f'<p>Fuente: <a href="{SOURCE}">setlist.fm</a></p></html>', encoding='utf-8')
    print(f'RSS generated with {len(rows)} concerts at {OUT_DIR / "rss.xml"}')


if __name__ == '__main__':
    main()
