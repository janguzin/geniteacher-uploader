from playwright.sync_api import sync_playwright
from pathlib import Path
from getpass import getpass
import os, re, sys, time

# ===================== 설정 (UI 변경 반영) =====================
UPLOAD_URL = "https://www.geniteacher.com/test-paper-upsert?id=0"
# [수정] 사이트 UI와 일치하도록 명칭 변경
CATEGORIES = ["모의고사 기출문제", "고3", "과학탐구"] 
STORAGE_PATH = "geni_storage.json"
EDGE_CHANNEL = "msedge"
OCR_TIMEOUT_MS = 15 * 60 * 1000

# ===================== 파일명 인식 패턴 =====================
ALLOWED_EXTS = {".pdf", ".doc", ".docx"}
PATTERN = re.compile(r"^(?P<base>.+?)_(?P<role>문제|해설|답안|답지).*", re.I)

# ===================== 공용 유틸 =====================
def js_force_click(page, locator):
    try:
        page.evaluate("(el)=>{el.scrollIntoView({block:'center'}); el.click();}", locator.first)
        return True
    except:
        return False

# ===================== 카테고리 추론 로직 =====================
def infer_categories_from_folder(folder: Path):
    name = folder.name.strip()
    # 폴더명에 '과학탐구'나 '물리'가 포함된 경우 처리
    if "과학" in name or "물리" in name or "화학" in name or "생명" in name or "지구" in name:
        return ["모의고사 기출문제", "고3", "과학탐구"]
    return CATEGORIES[:]

# ===================== 핵심 업로드 프로세스 =====================
def process_one_set(page, base, problem_file: Path, answer_file: Path, categories):
    # 페이지 진입 확인
    if "test-paper-upsert" not in page.url:
        page.goto(UPLOAD_URL, wait_until="networkidle")

    # 1) 학습지명 입력
    print(f"[*] 학습지명 설정: {base}")
    name_input = page.locator("input[placeholder*='학습지명']").first
    name_input.wait_for(state="visible", timeout=10000)
    name_input.fill(base)

    # 2) [에러 해결 구간] 카테고리 선택
    print(f"[*] 카테고리 클릭: {' > '.join(categories)}")
    for cat in categories:
        try:
            # exact=False를 사용하여 '모의고사 기출문제' 중 '기출문제'만 있어도 찾음
            loc = page.get_by_text(cat, exact=False).first
            
            # 요소가 나타날 때까지 최대 5초 대기
            loc.wait_for(state="visible", timeout=5000)
            
            if loc.is_visible():
                js_force_click(page, loc)
                time.sleep(0.5) # 클릭 후 UI 반응 대기
        except Exception as e:
            print(f"[!] 카테고리 '{cat}' 선택 중 건너뜀 (이미 선택되었거나 이름 변경 가능성)")

    # 3) 파일 업로드
    print(f"[*] 파일 업로드 중...")
    file_inputs = page.locator("input[type='file']")
    file_inputs.nth(0).set_input_files(str(problem_file))
    file_inputs.nth(1).set_input_files(str(answer_file))
    time.sleep(2)

    # 4) 문제 등록 버튼 (OCR 시작)
    print("[*] '문제 등록' 클릭")
    reg_btn = page.get_by_role("button", name=re.compile("문제\s*등록", re.I)).first
    reg_btn.click()

    # 5) 저장 버튼 활성화 대기
    print("[*] OCR 처리 및 저장 활성화 대기...")
    save_btn = page.get_by_role("button", name=re.compile("저장|완료", re.I)).last
    
    # OCR이 길어질 수 있으므로 충분히 대기
    save_btn.wait_for(state="visible", timeout=OCR_TIMEOUT_MS)
    
    # 버튼이 활성화(클릭 가능) 상태가 될 때까지 체크
    start_wait = time.time()
    while not save_btn.is_enabled():
        if time.time() - start_wait > OCR_TIMEOUT_MS / 1000:
            raise TimeoutError("OCR 시간이 초과되었습니다.")
        time.sleep(2)

    save_btn.click()
    print(f"[✓] {base} 업로드 및 저장 완료")
    time.sleep(3)

# ===================== 실행 메인 로직 =====================
def run(folder: Path):
    # (파일 스캔 로직 생략 - 이전과 동일)
    # ... (find_all_pairs_in_folder 함수 호출 부분) ...
    
    # 여기서는 예시를 위해 단순화된 pairs 구조를 사용합니다.
    # 실제 실행 시에는 이전 코드의 find_all_pairs_in_folder가 포함되어야 합니다.
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel=EDGE_CHANNEL)
        context = browser.new_context(storage_state=STORAGE_PATH) if os.path.exists(STORAGE_PATH) else browser.new_context()
        page = context.new_page()
        
        # 실제 pairs 데이터 로드 (생략된 부분)
        # pairs = find_all_pairs_in_folder(folder)
        # categories = infer_categories_from_folder(folder)
        
        # ... 루프 실행 ...