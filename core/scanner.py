from pathlib import Path
import re

class FileScanner:
    def __init__(self, pattern: str = r"^(?P<base>.+?)_(?P<role>문제|해설|답안|답지).*"):
        self.pattern = re.compile(pattern, re.I)

    def scan_pairs(self, folder_path: Path):
        files = list(folder_path.glob("*.*"))
        problem_files = {}
        answer_files = {}
        all_bases = set()

        for f in files:
            match = self.pattern.match(f.name)
            if not match: continue
            
            base = match.group("base")
            role = match.group("role")
            all_bases.add(base)

            if role == "문제":
                problem_files[base] = f
            elif role in ["해설", "답안", "답지"]:
                answer_files[base] = f

        valid_pairs = []
        errors = []

        # 5~6단계 검증 로직
        for base in sorted(all_bases):
            if base in problem_files and base in answer_files:
                valid_pairs.append({
                    "base": base,
                    "problem": problem_files[base],
                    "answer": answer_files[base]
                })
            else:
                missing = "해설" if base not in answer_files else "문제"
                errors.append(f"❌ [오류] {base}: {missing} 파일이 없습니다.")

        return valid_pairs, errors