from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PAGE_URL = "https://lostsaga-ko.valofe.com/main/main.asp"
CSS_SELECTOR = "#cont #charThumList > li > a > img"
OUTPUT_DIR = Path("./character_images")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),
    "Referer": PAGE_URL,
}


def get_image_url(img, base_url: str) -> str | None:
    """
    src, data-src, data-original 순서로 이미지 주소를 찾는다.
    상대경로는 절대경로로 변환한다.
    """
    image_src = (
        img.get("src")
        or img.get("data-src")
        or img.get("data-original")
    )

    if not image_src:
        return None

    return urljoin(base_url, image_src)


def make_filename(image_url: str, index: int) -> str:
    path = urlparse(image_url).path
    original_name = Path(path).name

    if not original_name:
        original_name = f"character_{index:03d}.jpg"

    return f"{index:03d}_{original_name}"


def download_character_images() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    response = session.get(PAGE_URL, timeout=20)
    response.raise_for_status()

    # 한국 사이트에서 인코딩이 정확히 감지되지 않을 경우를 대비
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")
    images = soup.select(CSS_SELECTOR)

    print(f"찾은 이미지 개수: {len(images)}")

    if not images:
        print("이미지를 찾지 못했습니다.")
        print("JavaScript로 생성되는 요소라면 아래 Selenium 방식을 사용해야 합니다.")
        return

    downloaded_urls: set[str] = set()

    for index, img in enumerate(images, start=1):
        image_url = get_image_url(img, PAGE_URL)

        if not image_url:
            print(f"[건너뜀] {index}: 이미지 URL 없음")
            continue

        if image_url in downloaded_urls:
            print(f"[중복 건너뜀] {image_url}")
            continue

        try:
            image_response = session.get(
                image_url,
                headers={"Referer": PAGE_URL},
                timeout=20,
            )
            image_response.raise_for_status()

            filename = make_filename(image_url, index)
            save_path = OUTPUT_DIR / filename
            save_path.write_bytes(image_response.content)

            downloaded_urls.add(image_url)
            print(f"[저장 완료] {save_path} <- {image_url}")

        except requests.RequestException as error:
            print(f"[다운로드 실패] {image_url}: {error}")


if __name__ == "__main__":
    download_character_images()