from pathlib import Path

from core.browser import BrowserManager
from core.page_objects import GeniUploaderPage
from core.scanner import FileScanner


def run_uploader(email, pw, folder_path, log_func):
    """
    GUI에서 호출되는 메인 업로더 함수
    """

    # ===============================
    # 1. 업로드 대상 폴더 확인
    # ===============================
    target_folder = Path(folder_path)

    if not target_folder.exists():
        log_func(f"❌ 폴더가 존재하지 않습니다: {target_folder}")
        return

    if not target_folder.is_dir():
        log_func(f"❌ 폴더 경로가 아닙니다: {target_folder}")
        return

    # ===============================
    # 2. 카테고리 파싱 (폴더명 기반)
    # ===============================
    # 예: 모의고사 기출문제_고3_과학탐구_물리1
    category_list = target_folder.name.split("_")
    log_func(f"[*] 카테고리 분석 결과: {' > '.join(category_list)}")

    # ===============================
    # 3. 파일 스캔 (_문제 / _해설 검증)
    # ===============================
    scanner = FileScanner()
    valid_pairs, scan_errors = scanner.scan_pairs(target_folder)

    # 오류 출력
    for err in scan_errors:
        log_func(err)

    if not valid_pairs:
        log_func("❌ [중단] 업로드 가능한 문제/해설 세트가 없습니다.")
        return

    log_func(f"[*] 총 {len(valid_pairs)}개의 세트 업로드를 시작합니다.")

    # ===============================
    # 4. 브라우저 실행
    # ===============================
    with BrowserManager(headless=False) as page:
        uploader = GeniUploaderPage(page)

        try:
            # ===============================
            # 5. 로그인 + 문제 관리 페이지 진입
            # ===============================
            uploader.login(email, pw)
            log_func("[✓] 로그인 및 문제 관리 페이지 진입 완료")

            # ===============================
            # 6. 파일 세트 반복 업로드
            # ===============================
            for idx, item in enumerate(valid_pairs, start=1):
                base_name = item["base"]
                problem_path = str(item["problem"])
                answer_path = str(item["answer"])

                log_func(f"\n[{idx}/{len(valid_pairs)}] 업로드 시작: {base_name}")

                # 안전장치: 항상 문제 관리 페이지에서 시작
                if "/test-papers" not in page.url:
                    page.goto(
                        "https://www.geniteacher.com/test-papers",
                        wait_until="networkidle"
                    )

                # 6-1. 문제 생성 버튼 클릭
                uploader.click_create_question()

                # 6-2. 카테고리 선택
                uploader.select_categories_hierarchical(category_list)

                # 6-3. 학습지명 입력 + 파일 업로드 + OCR + 저장
                uploader.upload_and_process(
                    base_name=base_name,
                    prob_path=problem_path,
                    ans_path=answer_path
                )

                log_func(f"[✓] 업로드 완료: {base_name}")

            # ===============================
            # 7. 전체 완료
            # ===============================
            log_func("\n🎉 모든 문제 업로드가 정상적으로 완료되었습니다.")

        except Exception as e:
            # 어떤 단계에서든 터지면 여기로 온다
            log_func(f"❌ 시스템 에러 발생: {str(e)}")


# ==================================
# 단독 실행 방지 (GUI에서만 호출)
# ==================================
if __name__ == "__main__":
    print("이 파일은 gui_main.py에서 호출되어야 합니다.")
