import json
import os
import random
import string
import time
from typing import Optional

from websocket import create_connection


class StudentWSClient:
    VALID_MODES = {"emoji", "question"}

    def __init__(
        self,
        ws_url: str,
        timeout: int = 5,
        favorites_file: str = "favorites.json",
    ):
        self.ws_url = ws_url
        self.timeout = timeout
        self.favorites_file = favorites_file
        self.favorites = self._load_favorites()

    def _send(self, payload: dict) -> bool:
        ws = None
        try:
            ws = create_connection(self.ws_url, timeout=self.timeout)
            ws.send(json.dumps(payload, ensure_ascii=False))
            print(f"전송 완료: {payload}")
            return True
        except Exception as e:
            print(f"전송 실패: {e}")
            return False
        finally:
            if ws is not None:
                ws.close()

    def _make_question_id(self) -> str:
        millis = int(time.time() * 1000)
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        return f"{millis}-{suffix}"

    def _validate_mode(self, mode: str) -> bool:
        if mode not in self.VALID_MODES:
            print("mode는 emoji 또는 question 이어야 합니다.")
            return False
        return True

    def _build_payload(self, mode: str, value: str) -> Optional[dict]:
        if not self._validate_mode(mode):
            return None

        if mode == "emoji":
            return {
                "type": "emoji",
                "emoji": value,
            }

        return {
            "type": "question",
            "text": value,
            "id": self._make_question_id(),
        }

    def send(self, mode: str, value: str) -> bool:
        payload = self._build_payload(mode, value)
        if payload is None:
            return False
        return self._send(payload)

    def send_emoji(self, emoji: str) -> bool:
        return self.send("emoji", emoji)

    def send_question(self, text: str) -> bool:
        return self.send("question", text)

    def _default_favorites(self) -> dict:
        return {"emoji": {}, "question": {}}

    def _load_favorites(self) -> dict:
        if not os.path.exists(self.favorites_file):
            return self._default_favorites()

        try:
            with open(self.favorites_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            normalized = self._default_favorites()
            normalized["emoji"] = data.get("emoji", {})
            normalized["question"] = data.get("question", {})
            return normalized

        except Exception as e:
            print(f"즐겨찾기 로드 실패: {e}")
            return self._default_favorites()

    def _save_favorites(self) -> None:
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"즐겨찾기 저장 실패: {e}")

    def _get_favorite_value(self, mode: str, name: str) -> Optional[str]:
        if not self._validate_mode(mode):
            return None

        value = self.favorites[mode].get(name)
        if value is None:
            print("해당 이름의 즐겨찾기가 없습니다.")
            return None
        return value

    def add_favorite(self, mode: str, name: str, value: str) -> None:
        if not self._validate_mode(mode):
            return

        self.favorites[mode][name] = value
        self._save_favorites()
        print(f"즐겨찾기 저장 완료: [{mode}] {name} -> {value}")

    def remove_favorite(self, mode: str, name: str) -> None:
        if not self._validate_mode(mode):
            return

        if name not in self.favorites[mode]:
            print("해당 이름의 즐겨찾기가 없습니다.")
            return

        del self.favorites[mode][name]
        self._save_favorites()
        print(f"즐겨찾기 삭제 완료: [{mode}] {name}")

    def list_favorites(self) -> None:
        print("\n=== 즐겨찾기 목록 ===")
        for mode in ("emoji", "question"):
            print(f"[{mode}]")
            if self.favorites[mode]:
                for name, value in self.favorites[mode].items():
                    print(f"- {name}: {value}")
            else:
                print("- 없음")
            print()

    def send_favorite(self, mode: str, name: str) -> bool:
        value = self._get_favorite_value(mode, name)
        if value is None:
            return False
        return self.send(mode, value)

    def send_repeat(self, mode: str, value: str, count: int, interval_sec: float = 1.0) -> None:
        if not self._validate_mode(mode):
            return

        if count < 1:
            print("count는 1 이상이어야 합니다.")
            return

        if interval_sec < 0:
            print("interval_sec는 0 이상이어야 합니다.")
            return

        for i in range(count):
            print(f"[{i + 1}/{count}] 전송 시도")
            self.send(mode, value)

            if i < count - 1:
                time.sleep(interval_sec)

    def send_favorite_repeat(
        self,
        mode: str,
        name: str,
        count: int,
        interval_sec: float = 1.0,
    ) -> None:
        value = self._get_favorite_value(mode, name)
        if value is None:
            return
        self.send_repeat(mode, value, count, interval_sec)


def prompt_menu() -> str:
    print("\n=== 메뉴 ===")
    print("1. 즉시 전송")
    print("2. 즐겨찾기 저장")
    print("3. 즐겨찾기 목록 조회")
    print("4. 즐겨찾기 전송")
    print("5. 반복 전송")
    print("6. 즐겨찾기 반복 전송")
    print("7. 즐겨찾기 삭제")
    print("q. 종료")
    return input("선택: ").strip().lower()


def prompt_mode() -> Optional[str]:
    raw = input("mode 선택 [1: emoji, 2: question]: ").strip()

    if raw == "1":
        return "emoji"
    if raw == "2":
        return "question"

    print("올바른 mode를 입력하세요.")
    return None


def prompt_non_empty(label: str) -> Optional[str]:
    value = input(f"{label}: ").strip()
    if not value:
        print(f"{label} 값은 비어 있을 수 없습니다.")
        return None
    return value


def prompt_count() -> Optional[int]:
    raw = input("반복 횟수: ").strip()
    try:
        count = int(raw)
        if count < 1:
            print("반복 횟수는 1 이상이어야 합니다.")
            return None
        return count
    except ValueError:
        print("정수를 입력하세요.")
        return None


def prompt_interval() -> Optional[float]:
    raw = input("전송 간격(초): ").strip()
    try:
        interval = float(raw)
        if interval < 0:
            print("전송 간격은 0 이상이어야 합니다.")
            return None
        return interval
    except ValueError:
        print("숫자를 입력하세요.")
        return None


def handle_send_now(client: StudentWSClient) -> None:
    mode = prompt_mode()
    if mode is None:
        return

    value = prompt_non_empty("전송할 값")
    if value is None:
        return

    client.send(mode, value)


def handle_add_favorite(client: StudentWSClient) -> None:
    mode = prompt_mode()
    if mode is None:
        return

    name = prompt_non_empty("즐겨찾기 이름")
    if name is None:
        return

    value = prompt_non_empty("저장할 값")
    if value is None:
        return

    client.add_favorite(mode, name, value)


def handle_send_favorite(client: StudentWSClient) -> None:
    mode = prompt_mode()
    if mode is None:
        return

    name = prompt_non_empty("전송할 즐겨찾기 이름")
    if name is None:
        return

    client.send_favorite(mode, name)


def handle_repeat_send(client: StudentWSClient) -> None:
    mode = prompt_mode()
    if mode is None:
        return

    value = prompt_non_empty("반복 전송할 값")
    if value is None:
        return

    count = prompt_count()
    if count is None:
        return

    interval = prompt_interval()
    if interval is None:
        return

    client.send_repeat(mode, value, count, interval)


def handle_repeat_favorite_send(client: StudentWSClient) -> None:
    mode = prompt_mode()
    if mode is None:
        return

    name = prompt_non_empty("반복 전송할 즐겨찾기 이름")
    if name is None:
        return

    count = prompt_count()
    if count is None:
        return

    interval = prompt_interval()
    if interval is None:
        return

    client.send_favorite_repeat(mode, name, count, interval)


def handle_remove_favorite(client: StudentWSClient) -> None:
    mode = prompt_mode()
    if mode is None:
        return

    name = prompt_non_empty("삭제할 즐겨찾기 이름")
    if name is None:
        return

    client.remove_favorite(mode, name)


def main():
    # "ws://ip:port/ws/student?room=<room_id>"
    ws_url = "ws://10.103.86.108:8000/ws/student?room=WJ8YLM"
    client = StudentWSClient(ws_url=ws_url)

    while True:
        menu = prompt_menu()

        if menu == "1":
            handle_send_now(client)
        elif menu == "2":
            handle_add_favorite(client)
        elif menu == "3":
            client.list_favorites()
        elif menu == "4":
            handle_send_favorite(client)
        elif menu == "5":
            handle_repeat_send(client)
        elif menu == "6":
            handle_repeat_favorite_send(client)
        elif menu == "7":
            handle_remove_favorite(client)
        elif menu == "q":
            print("프로그램을 종료합니다.")
            break
        else:
            print("올바른 메뉴를 선택하세요.")


if __name__ == "__main__":
    main()