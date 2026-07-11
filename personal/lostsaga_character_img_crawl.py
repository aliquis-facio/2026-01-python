from pathlib import Path
from urllib.parse import urljoin, urlparse
import re

import requests
from bs4 import BeautifulSoup


PAGE_URL = "https://lostsaga-ko.valofe.com/guide/class_list.asp"

SELECTORS = [
    "#cont #charThumList > li > a > img",
    "#charThumList > li > a > img",
    "#charThumList img",
]

OUTPUT_DIR = Path(__file__).resolve().parent / "character_images"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),
    "Referer": PAGE_URL,
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


def sanitize_filename(value: str) -> str:
    """Windows 파일명에 사용할 수 없는 문자를 제거한다."""
    value = re.sub(r'[<>:"/\\|?*]', "_", value)
    value = value.strip(" .")

    return value or "unknown"


def get_image_url(img) -> str | None:
    """일반 src 및 lazy-loading 속성에서 이미지 URL을 구한다."""
    for attribute in (
        "src",
        "data-src",
        "data-original",
        "data-lazy-src",
    ):
        value = img.get(attribute)

        if value and not value.startswith("data:"):
            return urljoin(PAGE_URL, value.strip())

    return None


def get_extension(image_url: str, content_type: str) -> str:
    suffix = Path(urlparse(image_url).path).suffix.lower()

    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return suffix

    content_type = content_type.lower()

    if "png" in content_type:
        return ".png"

    if "webp" in content_type:
        return ".webp"

    if "gif" in content_type:
        return ".gif"

    return ".jpg"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    response = session.get(PAGE_URL, timeout=30)
    response.raise_for_status()

    # 해당 사이트는 UTF-8을 사용하지만 잘못 감지될 때를 대비한다.
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    images = []
    matched_selector = None

    for selector in SELECTORS:
        elements = soup.select(selector)

        if elements:
            images = elements
            matched_selector = selector
            break

    print(f"[페이지 URL] {response.url}")
    print(f"[HTTP 상태] {response.status_code}")
    print(f"[선택자] {matched_selector}")
    print(f"[이미지 요소] {len(images)}개")

    if not images:
        debug_path = Path(__file__).resolve().parent / "class_list_debug.html"
        debug_path.write_text(response.text, encoding="utf-8")

        print("[실패] 용병 이미지 요소를 찾지 못했습니다.")
        print(f"[HTML 저장] {debug_path}")
        return

    downloaded_urls: set[str] = set()
    success_count = 0

    for index, img in enumerate(images, start=1):
        image_url = get_image_url(img)

        if not image_url:
            print(f"[건너뜀] {index}: 이미지 URL 없음")
            continue

        if image_url in downloaded_urls:
            print(f"[중복 건너뜀] {image_url}")
            continue

        # alt에 용병명이 들어 있다면 파일명으로 사용
        character_name = sanitize_filename(
            img.get("alt", "").strip()
            or f"character_{index:03d}"
        )

        try:
            image_response = session.get(
                image_url,
                headers={
                    "Referer": PAGE_URL,
                    "User-Agent": HEADERS["User-Agent"],
                },
                timeout=30,
            )
            image_response.raise_for_status()

            content_type = image_response.headers.get("Content-Type", "")

            if content_type and not content_type.startswith("image/"):
                print(
                    f"[건너뜀] 이미지가 아닌 응답: "
                    f"{content_type} / {image_url}"
                )
                continue

            extension = get_extension(image_url, content_type)

            filename = (
                f"{index:03d}_{character_name}{extension}"
            )
            save_path = OUTPUT_DIR / filename

            save_path.write_bytes(image_response.content)

            downloaded_urls.add(image_url)
            success_count += 1

            print(f"[저장 완료] {save_path.name}")
            print(f"             {image_url}")

        except requests.RequestException as error:
            print(f"[다운로드 실패] {character_name}")
            print(f"                 {image_url}")
            print(f"                 {error}")

    print()
    print(f"[완료] {success_count}개 다운로드")
    print(f"[저장 폴더] {OUTPUT_DIR}")


if __name__ == "__main__":
    main()