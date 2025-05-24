import pandas as pd
import fitz  # PyMuPDF

def extract_text_lines_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_lines = []
    for page in doc:
        page_text = page.get_text()
        text_lines.extend(page_text.splitlines())
    return text_lines

def load_rules(csv_path):
    df = pd.read_csv(csv_path)
    return list(zip(df["誤表記"], df["正表記"]))

def find_mistakes_by_line(lines, rules):
    results = []
    for wrong, correct in rules:
        line_hits = []
        total_count = 0
        for i, line in enumerate(lines, 1):
            count = line.count(wrong)
            if count > 0:
                line_hits.append((i, count))
                total_count += count
        if line_hits:
            results.append({
                "誤表記": wrong,
                "正表記": correct,
                "出現行": [line for line, _ in line_hits],
                "各行件数": [count for _, count in line_hits],
                "合計出現回数": total_count,
                "出現詳細": line_hits
            })
    return results

def main():
    pdf_path = "sample.docx"     # ←分析対象PDF
    rules_csv = "rules.csv"     # ←誤表記ルールCSV

    lines = extract_text_lines_from_pdf(pdf_path)
    rules = load_rules(rules_csv)
    mistakes = find_mistakes_by_line(lines, rules)
    
    print("【誤表記の検出結果】")
    for item in mistakes:
        print(f"\n●'{item['誤表記']}' → '{item['正表記']}'")
        print(f"   - 合計出現回数: {item['合計出現回数']}回")
        for line_num, count in item["出現詳細"]:
            print(f"{line_num}行目　{count}件")
        print()  # 空行で区切り
if __name__ == "__main__":
    main()
