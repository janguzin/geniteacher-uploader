import re
import time
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

class GeniUploaderPage:
    def __init__(self, page: Page):
        self.page = page
        # 공통 Selector
        self.name_input = page.locator("input[placeholder*='학습지명']")
        self.file_input = page.locator("input[type='file']")
        # 버튼 Selector (강화됨)
        self.create_btn = page.locator("button:has-text('문제 생성')")
        self.reg_button = page.get_by_role("button", name=re.compile("문제\s*등록", re.I))

    def navigate(self, url: str):
        """페이지 이동 유틸리티"""
        if url not in self.page.url:
            self.page.goto(url, wait_until="networkidle")

    def login(self, user_email: str, user_pw: str):
        """로그인 및 리스트 페이지 강제 진입"""
        print(f"[*] 로그인 시도: {user_email}")
        self.page.goto("https://www.geniteacher.com/login", wait_until="networkidle")
        
        if "/login" not in self.page.url:
            print("[✓] 이미 로그인 상태입니다.")
            return

        self.page.get_by_placeholder("이메일").fill(user_email)
        self.page.get_by_placeholder("비밀번호").fill(user_pw)
        self.page.get_by_role("button", name="로그인", exact=True).click()
        
        # 로그인 후 리스트 페이지로 강제 이동 및 확인
        time.sleep(2)
        self.page.goto("https://www.geniteacher.com/test-papers", wait_until="networkidle")
        try:
            self.create_btn.wait_for(state="visible", timeout=10000)
            print("[✓] 로그인 및 문제 관리 페이지 진입 완료")
        except:
            print("[!] 페이지 진입 확인 지연 중...")

    def click_create_question(self):
        """4단계: '문제 생성' 버튼 강제 클릭"""
        print("[*] '문제 생성' 버튼 클릭 시도...")
        try:
            # 1. 일반 클릭 시도
            self.create_btn.first.wait_for(state="visible", timeout=10000)
            self.create_btn.first.click()
        except:
            # 2. 실패 시 자바스크립트로 강제 클릭 (가장 확실함)
            print("[!] 일반 클릭 실패 -> JS 강제 클릭 실행")
            self.page.evaluate("document.querySelector('button:has-text(\"문제 생성\")').click()")
        
        # 입력창이 나타날 때까지 대기
        self.name_input.first.wait_for(state="visible", timeout=10000)

    def select_categories_hierarchical(self, categories: list):
        """8단계: 폴더명 기반 계층적 카테고리 선택"""
        for cat in categories:
            try:
                # 텍스트가 정확히 일치하는 요소를 찾아 클릭
                loc = self.page.get_by_text(cat, exact=True).first
                loc.wait_for(state="visible", timeout=3000)
                # 스크롤 후 클릭
                self.page.evaluate("(el) => { el.scrollIntoView({block:'center'}); el.click(); }", loc)
                time.sleep(0.5)
                print(f"  - [카테고리] {cat} 선택 완료")
            except:
                print(f"  - [카테고리] {cat} 찾기 실패 (이미 선택되었거나 없음)")

    def upload_and_process(self, base_name, prob_path, ans_path, timeout_ms=900000):
        """7~13단계: 업로드부터 OCR 저장 후 리스트 복귀까지"""
        # 7. 학습지명 입력
        self.name_input.first.fill(base_name)
        
        # 9. 파일 업로드 (0:문제, 1:해설)
        self.file_input.nth(0).set_input_files(prob_path)
        self.file_input.nth(1).set_input_files(ans_path)
        time.sleep(1)

        # 10. 등록 버튼 클릭
        self.reg_button.wait_for(state="visible")
        self.reg_button.click()
        
        # 11~12. OCR 대기 (수정 페이지 step2로 이동할 때까지)
        print(f"[*] {base_name}: OCR 변환 대기 중 (최대 15분)...")
        self.page.wait_for_url("**/upsert-step2**", timeout=timeout_ms)
        
        # 13. 우측 상단 X 버튼 클릭 (저장 후 종료)
        time.sleep(3)
        print("[*] 저장 및 리스트 복귀 시도...")
        try:
            # 영상 속 위치의 X 버튼(닫기 아이콘) 클릭
            close_btn = self.page.locator("button").filter(has=self.page.locator("svg, i")).last
            close_btn.click()
        except:
            # 클릭 실패 시 ESC 키로 저장 팝업 유도 또는 강제 이동
            self.page.keyboard.press("Escape")
        
        # 리스트 페이지 복귀 확인
        self.page.wait_for_url("**/test-papers", timeout=10000)
        print(f"[✓] {base_name} 업로드 프로세스 완료")