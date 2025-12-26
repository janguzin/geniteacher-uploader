import os
from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self, storage_path="geni_storage.json", headless=False):
        self.storage_path = storage_path
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None

    def __enter__(self):
        # Playwright 시작
        self.playwright = sync_playwright().start()
        # Edge 브라우저 실행 (channel="msedge")
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, 
            channel="msedge"
        )
        
        # 세션 정보가 있으면 불러오고, 없으면 새 컨텍스트 생성
        if os.path.exists(self.storage_path):
            self.context = self.browser.new_context(storage_state=self.storage_path)
        else:
            self.context = self.browser.new_context()
            
        return self.context.new_page()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 작업 완료 후 브라우저 닫기
        if self.context:
            # 현재 로그인 상태를 파일로 저장 (다음 실행 시 로그인 생략 가능)
            self.context.storage_state(path=self.storage_path)
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()