import json, time, random, string, os
from websocket import create_connection


class StudentWSClient:
    def __init__(self, ws_url: str, timeout: int = 5, favorites_file: str = "favorites.json"):
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
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        return f"{millis}-{suffix}"

    def _load_favorites(self) -> dict:
        if not os.path.exists(self.favorites_file):
            return {"emoji": {}, "question": {}}
        
        try:
            with open(self.favorites_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "emoji" not in data:
                data["emoji"] = {}
            if "question" not in data:
                data["question"] = {}
            
            return data
        except Exception as e:
            print(f"즐겨찾기 로드 실패: {e}")
            return {"emoji": {}, "question": {}}
    
    def _save_favorites(self) -> None:
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"즐겨찾기 저장 실패: {e}")
    
    def add_favorite(self, mode: str, name: str, value: str) -> None:
        if mode not in ("emoji", "question"):
            print("mode는 emoji 또는 question 이어야 합니다.")
            return

        self.favorites[mode][name] = value
        self._save_favorites()
        print(f"즐겨찾기 저장 완료: [{mode}] {name} -> {value}")

    def remove_favorite(self, mode: str, name: str) -> None:
        if mode not in ("emoji", "question"):
            print("mode는 emoji 또는 question 이어야 합니다.")
            return

        if name not in self.favorites[mode]:
            print("해당 이름의 즐겨찾기가 없습니다.")
            return

        del self.favorites[mode][name]
        self._save_favorites()
        print(f"즐겨찾기 삭제 완료: [{mode}] {name}")

    def list_favorites(self) -> None:
        print("\n=== 즐겨찾기 목록 ===")

        print("[emoji]")
        if self.favorites["emoji"]:
            for name, value in self.favorites["emoji"].items():
                print(f"- {name}: {value}")
        else:
            print("- 없음")

        print("\n[question]")
        if self.favorites["question"]:
            for name, value in self.favorites["question"].items():
                print(f"- {name}: {value}")
        else:
            print("- 없음")

        print()

    def send_favorite(self, mode: str, name: str) -> bool:
        if mode not in ("emoji", "question"):
            print("mode는 emoji 또는 question 이어야 합니다.")
            return False

        if name not in self.favorites[mode]:
            print("해당 이름의 즐겨찾기가 없습니다.")
            return False

        value = self.favorites[mode][name]

        if mode == "emoji":
            return self.send_emoji(value)
        else:
            return self.send_question(value)
    
    def send_favorite_repeat(self, mode: str, name: str, count: int, interval_sec: float = 1.0) -> None:
        if mode not in ("emoji", "question"):
            print("mode는 emoji 또는 question 이어야 합니다.")
            return

        if name not in self.favorites[mode]:
            print("해당 이름의 즐겨찾기가 없습니다.")
            return

        value = self.favorites[mode][name]
        self.send_repeat(mode, value, count, interval_sec)

    def send_repeat(self, mode: str, value: str, count: int, interval_sec: float = 1.0) -> None:
        if count < 1:
            print("count는 1 이상이어야 합니다.")
            return

        if interval_sec < 0:
            print("interval_sec는 0 이상이어야 합니다.")
            return

        for i in range(count):
            print(f"[{i + 1}/{count}] 전송 시도")
            if mode == "emoji":
                self.send_emoji(value)
            elif mode == "question":
                self.send_question(value)
            else:
                print("지원하지 않는 mode입니다. emoji 또는 question만 가능합니다.")
                return

            if i < count - 1:
                time.sleep(interval_sec)

    def send_emoji(self, emoji: str) -> bool:
        payload = {
            "type": "emoji",
            "emoji": emoji
        }
        return self._send(payload)

    def send_question(self, text: str) -> bool:
        payload = {
            "type": "question",
            "text": text,
            "id": self._make_question_id()
        }
        return self._send(payload)

if __name__ == "__main__":
    # url 값에 맞게 변경하기
    url = "ws://10.103.78.155:8000/ws/student?room=SU514A"

    client = StudentWSClient(ws_url=url)

    while(True):
        mode = input("[mode] emoji: 1, question: 2\n")
        query = input("query: ")
        if mode == "1":
            client.send_emoji(query)
        elif mode == "2":
            client.send_question(query)
