import os
import sys
import time
from dotenv import load_dotenv

# Ensure core is importable
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.graph import build_planner_graph
from app import extract_headline, safe_filename, get_merged_feedback

load_dotenv()

brief_input = "스텔라루멘 코인 분석과 전망에 대한 리포트"
designer_feedback = get_merged_feedback()

initial_state = {
    "brief": brief_input,
    "designer_feedback": designer_feedback
}

print("🚀 Starting AI Creative Director Pipeline for Stellar Lumens (XLM)...")
app = build_planner_graph()

full_state = {}
try:
    for output in app.stream(initial_state):
        for key, value in output.items():
            print(f"✅ Completed Node: [{key}]")
            full_state.update(value)
except Exception as e:
    print(f"❌ Error during pipeline execution: {e}")
    sys.exit(1)

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
            
    print(f"\n🎉 [SUCCESS] Saved report as 'reports/{safe_name}.md'")
    print(f"🎉 [SUCCESS] Saved PPT parsing code as 'reports/{safe_name}.txt'")
    print(f"🎉 [SUCCESS] Saved Evaluation report as 'reports/{safe_name}_eval.md'")
    
    # Also save to temp_ppt_code.txt for quick access
    with open("temp_ppt_code.txt", "w", encoding="utf-8") as f:
        f.write(ppt_content)
        
    print("\n--- QA Feedback ---")
    print(full_state.get('qa_feedback', ''))
else:
    print("❌ Failed to generate report or PPT parsing code.")
