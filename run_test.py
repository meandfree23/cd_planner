import os
import time
from core.graph import build_planner_graph
from app import extract_headline, safe_filename, get_merged_feedback
from dotenv import load_dotenv

load_dotenv()

brief_input = "2026년 대한민국 지방선거를 대비한 정당 필승 전략 및 캠페인 기획"
designer_feedback = get_merged_feedback()

initial_state = {
    "brief": brief_input,
    "designer_feedback": designer_feedback
}

app = build_planner_graph()

print("Running pipeline...")
full_state = {}
for output in app.stream(initial_state):
    for key, value in output.items():
        print(f"Completed node: {key}")
        full_state.update(value)

# Saving logic
if "final_report" in full_state and "ppt_code" in full_state:
    report_content = full_state["final_report"]
    ppt_content = full_state["ppt_code"]
    eval_content = f"{full_state.get('qa_feedback', '')}\n\n---\n\n{full_state.get('evaluation_report', '')}"
    
    if not os.path.exists("reports"):
        os.makedirs("reports")
    
    headline = extract_headline(report_content, brief_input)
    safe_name = safe_filename(headline)
    
    base_safe_name = safe_name
    counter = 1
    while os.path.exists(f"reports/{safe_name}.md"):
        safe_name = f"{base_safe_name}_{counter}"
        counter += 1
        
    md_filename = f"reports/{safe_name}.md"
    txt_filename = f"reports/{safe_name}.txt"
    eval_filename = f"reports/{safe_name}_eval.md"
    
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(f"# Campaign Brief\n\n{brief_input}\n\n---\n\n")
        f.write(report_content)
    
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(ppt_content)
        
    if eval_content:
        with open(eval_filename, "w", encoding="utf-8") as f:
            f.write(eval_content)

    print(f"\n[SUCCESS] Saved as {safe_name}")
    print("\n--- QA Feedback ---")
    print(full_state.get('qa_feedback', ''))
    
    # Save the ppt code to a txt file to copy easily
    with open("temp_ppt_code.txt", "w", encoding="utf-8") as f:
        f.write(ppt_content)
