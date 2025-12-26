import os
from pathlib import Path
from core.browser import BrowserManager
from core.page_objects import GeniUploaderPage
from core.scanner import FileScanner

def run_uploader(email, pw, folder_path, log_func):
    target_folder = Path(folder_path)
    
    # 8단계: 폴더명에서 카테고리 리스트 추출
    category_list = target_folder.name.split('_')
    log_func(f"[*] 카테고리 분석 결과: {' > '.join(category_list)}")

    # 5~6단계: 파일 스캔 및 검증
    # [핵심] 리턴값이 2개이므로 반드시 변수 2개로 나눠 받아야 에러가 안 납니다.
    scanner = FileScanner()
    valid_pairs, scan_errors = scanner.scan_pairs(target_folder)
    
    for err in scan_errors:
        log_func(err)
    
    if not valid_pairs:
        log_func("❌ [중단] 업로드할 파일 세트가 없습니다.")
        return

    log_func(f"[*] 총 {len(valid_pairs)}개의 세트 작업을 시작합니다.")

    with BrowserManager(headless=False) as page:
        uploader = GeniUploaderPage(page)
        
        try:
            # 2~3단계: 로그인 및 진입
            uploader.login(email, pw)
            log_func("[✓] 로그인 및 문제 관리 페이지 진입 성공")

            # 14단계: 전체 반복 루프
            for i, item in enumerate(valid_pairs, 1):
                base_name = item['base']
                log_func(f"\n[{i}/{len(valid_pairs)}] '{base_name}' 업로드 진행 중...")
                
                # 매 루프 시작 시 목록 페이지 주소 확인 (안전장치)
                if "/test-papers" not in page.url:
                    page.goto("https://www.geniteacher.com/test-papers", wait_until="networkidle")
                
                # 4단계: 문제 생성 클릭
                uploader.click_create_question()
                
                # 8단계: 카테고리 선택
                uploader.select_categories_hierarchical(category_list)
                
                # 7~13단계: 입력, 업로드, OCR, 저장
                uploader.upload_and_process(
                    base_name, 
                    str(item['problem']), 
                    str(item['answer'])
                )
                
            log_func("\n[★] 모든 파일 업로드 작업이 완료되었습니다!")
            
        except Exception as e:
            log_func(f"❌ [에러 발생] {str(e)}")

if __name__ == "__main__":
    # 이 파일은 gui_main.py에 의해 호출되지만 단독 테스트용으로 남겨둠
    pass