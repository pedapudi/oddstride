"""Exercise plate downloads, fabrication filters and the part orientation control."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8768/review/'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                                args=['--no-sandbox', '--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width': 1500, 'height': 1050})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + 'manufacturing.html')
    page.wait_for_function('window.manufacturingPlan && document.querySelectorAll("#parts tr").length === window.manufacturingPlan.parts.length')
    page.wait_for_function('Array.from(document.querySelectorAll("#plates img")).every(i => i.complete && i.naturalWidth > 0)')
    plate_count = page.evaluate('window.manufacturingPlan.plates.length')
    assert page.locator('#plates img').count() == plate_count
    page.select_option('#route', 'printed')
    printed_count = page.evaluate('window.manufacturingPlan.parts.filter(p => p.route === "printed").length')
    assert page.locator('#parts tr').count() == printed_count
    page.fill('#search', 'front_fascia')
    assert page.locator('#parts tr').count() == 1
    page.fill('#search', '')
    page.select_option('#route', '')
    for link in page.locator('.actions a, #plates a').all():
        url = urljoin(page.url, link.get_attribute('href'))
        assert page.request.get(url).status == 200, url
    page.screenshot(path=str(ROOT / 'output/manufacturing-preview.png'), full_page=True)
    page.goto(BASE + 'parts.html#front_fascia')
    page.wait_for_function('window.currentPart && window.currentPart.id === "front_fascia"')
    page.click('#print-orientation')
    assert page.locator('#print-orientation').inner_text() == 'Assembly coordinates'
    page.screenshot(path=str(ROOT / 'output/fascia-print-orientation.png'))
    page.click('#print-orientation')
    assert page.locator('#print-orientation').inner_text() == 'Print orientation'
    assert not errors, errors
    result = {'model_sha256': hashlib.sha256((ROOT / 'output/model.json').read_bytes()).hexdigest(),
              'plate_previews': plate_count, 'printed_parts': printed_count, 'downloads_ok': True,
              'orientation_toggle_ok': True, 'page_errors': errors}
    (ROOT / 'output/manufacturing-browser-checks.json').write_text(json.dumps(result, indent=2))
    browser.close()
print('Manufacturing filters, plate previews/downloads and part orientation control passed.')
