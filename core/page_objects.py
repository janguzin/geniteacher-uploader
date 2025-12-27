import re
import time
from playwright.sync_api import Page


class GeniUploaderPage:
    def __init__(self, page: Page):
        self.page = page

        # 공통 Selector
        self.name_input = page.locator("input[placeholder*='학습지명']")
        self.file_input = page.locator("input[type='file']")
        self.create_btn = page.get_by_role("button", name="문제 생성")
        self.reg_button = page.get_by_role("button", name=re.compile("문제\s*등록", re.I))

    def navigate(self, url: str):
        if url not in self.page.url:
            self.page.goto(url, wait_until="networkidle")

    # =========================
    # Login
    # =========================
    def login(self, user_email: str, user_pw: str):
        print(f"[*] 로그인 시도: {user_email}")
        self.page.goto("https://www.geniteacher.com/login", wait_until="networkidle")

        # 이미 로그인된 경우
        if "/login" not in self.page.url:
            print("[✓] 이미 로그인 상태")
            return

        self.page.get_by_placeholder("이메일").fill(user_email)
        self.page.get_by_placeholder("비밀번호").fill(user_pw)
        self.page.get_by_role("button", name="로그인", exact=True).click()

        # 로그인 성공 기준: 메뉴 등장
        self.page.wait_for_selector("text=문제 관리", timeout=15000)
        print("[✓] 로그인 성공")

        # 문제 관리 페이지로 명시적 이동
        self.page.goto("https://www.geniteacher.com/test-papers", wait_until="networkidle")
        self.create_btn.wait_for(state="visible", timeout=10000)
        print("[✓] 문제 관리 페이지 진입 완료")

        # 문제 생성 페이지로 명시적 이동
        self.page.goto("https://www.geniteacher.com/test-paper-upsert?id=0", wait_until="networkidle")
        self.create_btn.wait_for(state="visible", timeout=10000)
        print("[✓] 문제 생성 페이지 진입 완료")

    # =========================
    # 문제 생성
    # =========================
    def click_create_question(self):
        print("[*] '문제 생성' 버튼 클릭")
        self.create_btn.wait_for(state="visible", timeout=10000)
        self.create_btn.click()

        # ❗ URL 바뀌는 거 기다리지 말고
        # ❗ 입력창 등장만 확인
        self.name_input.wait_for(state="visible", timeout=10000)
        print("[✓] 문제 생성 폼 열림")

    # =========================
    # 카테고리
    # =========================
    def select_categories_hierarchical(self, categories: list):
        for cat in categories:
            try:
                loc = self.page.get_by_text(cat, exact=True).first
                loc.wait_for(state="visible", timeout=3000)
                loc.scroll_into_view_if_needed()
                loc.click()
                time.sleep(0.4)
                print(f"  - 카테고리 선택: {cat}")
            except:
                print(f"  - 카테고리 스킵: {cat}")

    # =========================
    # 업로드 + OCR
    # =========================
    def upload_and_process(self, base_name, prob_path, ans_path, timeout_ms=900000):
        self.name_input.fill(base_name)

        self.file_input.nth(0).set_input_files(prob_path)
        self.file_input.nth(1).set_input_files(ans_path)
        time.sleep(1)

        self.reg_button.wait_for(state="visible", timeout=10000)
        self.reg_button.click()

        print(f"[*] {base_name}: OCR 처리 대기")
        self.page.wait_for_url("**/upsert-step2**", timeout=timeout_ms)

        time.sleep(2)
        print("[*] 저장 후 리스트 복귀")

        # X 버튼 (안정적으로 role 기반)
        close_btn = self.page.get_by_role("button").filter(has_text="X").first
        close_btn.click()

        self.page.wait_for_url("**/test-papers", timeout=15000)
        print(f"[✓] {base_name} 완료")
