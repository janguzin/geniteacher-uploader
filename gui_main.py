import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path

# 우리가 만든 로직 임포트
from core.browser import BrowserManager
from core.page_objects import GeniUploaderPage
from core.scanner import FileScanner
import yaml

class UploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GeniTeacher 자동 업로더")
        self.root.geometry("500x550")

        # 1. ID 입력
        tk.Label(root, text="아이디").pack(pady=5)
        self.ent_id = tk.Entry(root, width=40)
        self.ent_id.pack()

        # 2. PW 입력
        tk.Label(root, text="비밀번호").pack(pady=5)
        self.ent_pw = tk.Entry(root, width=40, show="*")
        self.ent_pw.pack()

        # 3. 폴더 선택
        tk.Label(root, text="업로드할 폴더").pack(pady=5)
        self.ent_path = tk.Entry(root, width=40)
        self.ent_path.pack()
        tk.Button(root, text="폴더 찾기", command=self.browse_folder).pack(pady=5)

        # 4. 로그 출력창
        tk.Label(root, text="진행 상황").pack(pady=5)
        self.log_text = tk.Text(root, height=15, width=60)
        self.log_text.pack(padx=10)

        # 5. 실행 버튼
        self.btn_run = tk.Button(root, text="업로드 시작", command=self.start_thread, 
                                 bg="green", fg="white", height=2, width=20)
        self.btn_run.pack(pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.ent_path.delete(0, tk.END)
            self.ent_path.insert(0, folder)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def start_thread(self):
        # UI가 멈추지 않게 별도 쓰레드에서 실행
        t = threading.Thread(target=self.run_uploader)
        t.daemon = True
        t.start()

    def run_uploader(self):
        user_id = self.ent_id.get()
        user_pw = self.ent_pw.get()
        folder_path = self.ent_path.get()

        if not user_id or not user_pw or not folder_path:
            messagebox.showwarning("입력 누락", "모든 정보를 입력해주세요.")
            return

        self.btn_run.config(state="disabled")
        self.log("[*] 작업을 시작합니다...")

        try:
            with open("config/settings.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            with BrowserManager(headless=False) as page:
                uploader = GeniUploaderPage(page)
                
                # 로그인 수행
                uploader.login(user_id, user_pw)
                
                scanner = FileScanner(r"^(?P<base>.+?)_(?P<role>문제|해설|답안|답지).*")
                pairs = scanner.scan_pairs(Path(folder_path))
                
                self.log(f"[*] 발견된 세트: {len(pairs)}개")

                for item in pairs:
                    try:
                        self.log(f"[*] 업로드 중: {item['base']}")
                        uploader.navigate(config['urls']['upload_url'])
                        uploader.enter_test_name(item['base'])
                        uploader.select_categories_flexibly(config['category_keywords'])
                        uploader.upload_files(str(item['problem']), str(item['answer']))
                        uploader.start_ocr()
                        uploader.wait_and_save(config['timeouts']['ocr_ms'])
                        self.log(f"[✓] 완료: {item['base']}")
                    except Exception as e:
                        self.log(f"[!] 에러 ({item['base']}): {e}")

            self.log("[*] 모든 작업이 끝났습니다.")
        except Exception as e:
            self.log(f"[!!!] 시스템 에러: {e}")
        finally:
            self.btn_run.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = UploaderApp(root)
    root.mainloop()