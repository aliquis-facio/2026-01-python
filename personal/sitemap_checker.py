import csv
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

SITEMAP_URL = "https://aliquis-facio.github.io/sitemap.xml"
OUTPUT_CSV = "C:/Users/jeony/Desktop/Code/2026-01-python/personal/sitemap_url_check_result.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SitemapChecker/1.0)"
}

# 연결 5초, 응답 읽기 10초
TIMEOUT = (5, 10)

def fetch_sitemap(sitemap_url: str) -> str:
    response = requests.get(
        sitemap_url,
        headers=HEADERS,
        timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.text


def extract_loc_urls(sitemap_xml: str) -> list[str]:
    root = ET.fromstring(sitemap_xml)

    urls = []

    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            urls.append(elem.text.strip())

    return urls


def check_url(url: str) -> dict:
    try:
        # 1차: HEAD 요청
        response = requests.head(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        # 일부 서버는 HEAD를 제대로 지원하지 않음
        if response.status_code in [403, 405]:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
                stream=True
            )
            response.close()

        redirect_chain = " -> ".join(
            [f"{r.status_code}:{r.url}" for r in response.history]
        )

        return {
            "url": url,
            "status_code": response.status_code,
            "final_url": response.url,
            "is_redirected": len(response.history) > 0,
            "redirect_count": len(response.history),
            "redirect_chain": redirect_chain,
            "ok": 200 <= response.status_code < 300,
            "error": ""
        }

    except requests.exceptions.Timeout:
        return {
            "url": url,
            "status_code": "TIMEOUT",
            "final_url": "",
            "is_redirected": "",
            "redirect_count": "",
            "redirect_chain": "",
            "ok": False,
            "error": "요청 시간 초과"
        }

    except requests.exceptions.TooManyRedirects:
        return {
            "url": url,
            "status_code": "TOO_MANY_REDIRECTS",
            "final_url": "",
            "is_redirected": True,
            "redirect_count": "",
            "redirect_chain": "",
            "ok": False,
            "error": "리디렉션이 너무 많음"
        }

    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "status_code": "REQUEST_ERROR",
            "final_url": "",
            "is_redirected": "",
            "redirect_count": "",
            "redirect_chain": "",
            "ok": False,
            "error": str(e)
        }


def load_checked_urls(csv_path: str) -> set[str]:
    path = Path(csv_path)

    if not path.exists():
        return set()

    checked = set()

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            checked.add(row["url"])

    return checked


def append_result(csv_path: str, result: dict):
    path = Path(csv_path)

    fieldnames = [
        "url",
        "status_code",
        "final_url",
        "is_redirected",
        "redirect_count",
        "redirect_chain",
        "ok",
        "error"
    ]

    file_exists = path.exists()

    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)


def main():
    print(f"사이트맵 가져오는 중: {SITEMAP_URL}")

    sitemap_xml = fetch_sitemap(SITEMAP_URL)
    urls = extract_loc_urls(sitemap_xml)

    checked_urls = load_checked_urls(OUTPUT_CSV)

    print(f"총 URL 수: {len(urls)}")
    print(f"이미 검사한 URL 수: {len(checked_urls)}")
    print("-" * 80)

    for index, url in enumerate(urls, start=1):
        if url in checked_urls:
            print(f"[{index}/{len(urls)}] 이미 검사함: {url}")
            continue

        print(f"[{index}/{len(urls)}] 검사 중: {url}")

        result = check_url(url)
        append_result(OUTPUT_CSV, result)

        print(f"  status_code : {result['status_code']}")
        print(f"  final_url   : {result['final_url']}")
        print(f"  redirected  : {result['is_redirected']}")
        print(f"  ok          : {result['ok']}")

        if result["error"]:
            print(f"  error       : {result['error']}")

        print("-" * 80)

        time.sleep(0.2)

    print(f"\n검사 완료: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()