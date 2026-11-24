from pathlib import Path

import os
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright

import csv

ROOT = Path(__file__).resolve().parents[1]

with sync_playwright() as p, TemporaryDirectory() as temp:
    browser = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH"))
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto((ROOT / "index.html").as_uri())

    def upload_csv(data):
        page.locator("#file").set_input_files(
            dict(name="data.csv", mimeType="text/csv", buffer=data)
        )

    upload_csv(b'City,Note\r\n"  new  york  ","a,b"\r\nParis,"a""b\nc"\r\n')
    page.locator("#spaces").check()
    page.locator("#letter").select_option("Uppercase")
    assert "2 of 2" in page.locator("#status").inner_text()
    dest = Path(temp) / "data.csv"
    with page.expect_download() as download:
        page.locator("#save").click()
    download.value.save_as(dest)
    with dest.open(encoding="utf-8-sig", newline="") as f:
        assert list(csv.reader(f)) == [
            ["City", "Note"],
            ["NEW YORK", "a,b"],
            ["PARIS", 'a"b\nc'],
        ]
    upload_csv(b'a,b\n"broken')
    page.wait_for_function(
        "document.getElementById('status').textContent.includes('Unclosed')"
    )
    assert page.locator("#save").is_disabled()
    assert not errors, errors
    browser.close()
