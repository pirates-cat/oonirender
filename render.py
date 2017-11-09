#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Usage:
#
#   python3 render.py urls.txt
#   markdown2 --extras code-friendly,fenced-code-blocks output.md > output.html
#   weasyprint output.html output.pdf

from bs4 import BeautifulSoup
from markdown2 import markdown
from urllib.parse import parse_qs, quote, urlparse, urlencode
import json
import requests
import sys

tpl = u"""# Caso {case_id:03d}

**Dominio:** [{domain}]({domain})

**Fecha de la prueba:** {date}

**Red (ASN):** {asn_name} ({asn_id})

**Resultado:**

```html
{content}
```

[**Fuente**]({src_url})
<hr>
"""

def render(ooni_url, ix):
    src = urlparse(ooni_url)
    where = quote(json.dumps({
        'where': {
            'id': src.path.split('/')[2],
            'input': parse_qs(src.query)['input'][0]
        }
    }))
    dst = 'https://explorer.ooni.torproject.org/api/reports?filter={}'.format(where)
    probe = requests.get(dst).json()[0]
    asn_data = requests.get('https://explorer.ooni.torproject.org/api/reports/asnName?asn={}'.format(probe['probe_asn'])).json()
    if len(asn_data) == 0:
        asn_name = probe['probe_asn']
    else:
        asn_name = asn_data[0]['name']
    content = probe['test_keys']['requests'][0]['response']['body']
    soup = BeautifulSoup(content, 'html.parser')
    return tpl.format(
        case_id=ix,
        domain=probe['input'],
        date=probe['measurement_start_time'],
        asn_name=asn_name,
        asn_id=probe['probe_asn'],
        content=soup.prettify(),
        src_url=src.geturl()
    )

with open(sys.argv[1]) as f:
    urls = f.readlines()
    md_content = ''
    for ix in range(len(urls)):
        md_content += render(urls[ix].strip(), ix)
    raw_html = markdown(md_content, extras=['code-friendly', 'fenced-code-blocks'])
    with open('output.md', 'w+') as md:
        md.write(md_content)
