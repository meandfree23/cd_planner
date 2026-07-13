from langgraph.graph import StateGraph, END
from core.state import PlannerState
from core.nodes import web_search_node, parallel_ideation_node, synthesize_node, hook_strategy_node, parallel_report_node, report_merge_node, qa_judge_node, ppt_code_node, evaluation_node, evolution_proof_node

def build_planner_graph():
    """CD 플래너 에이전트의 워크플로우 그래프를 생성하고 컴파일합니다. (병렬 멀티 에이전트 적용)"""
    
    workflow = StateGraph(PlannerState)
    
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("parallel_ideation", parallel_ideation_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("hook_strategy", hook_strategy_node)
    workflow.add_node("parallel_report", parallel_report_node)
    workflow.add_node("report_merge", report_merge_node)
    workflow.add_node("qa_judge", qa_judge_node)
    workflow.add_node("ppt_code", ppt_code_node)
    workflow.add_node("evaluation", evaluation_node)
    workflow.add_node("evolution_proof", evolution_proof_node)
    
    workflow.set_entry_point("web_search")
    workflow.add_edge("web_search", "parallel_ideation")
    workflow.add_edge("parallel_ideation", "synthesize")
    workflow.add_edge("synthesize", "hook_strategy")
    workflow.add_edge("hook_strategy", "parallel_report")
    workflow.add_edge("parallel_report", "report_merge")
    workflow.add_edge("report_merge", "qa_judge")
    workflow.add_edge("qa_judge", "ppt_code")
    workflow.add_edge("ppt_code", "evaluation")
    
    import re
    def should_revise(state: PlannerState) -> str:
        report = state.get("evaluation_report", "")
        score = 10.0
        match = re.search(r'종합\s*점수[^0-9]*([0-9.]+)', report)
        if match:
            try:
                score = float(match.group(1))
            except ValueError:
                pass
                
        print(f"--- [ROUTER] Evaluation Score: {score} / 10 ---")
        revision_count = state.get("revision_count", 0)
        
        if score < 9.0 and revision_count < 2:
            print(f"--- [ROUTER] Score below 9.0. Triggering Revision {revision_count + 1} / 2 ---")
            return "parallel_ideation"
        else:
            print("--- [ROUTER] Score acceptable or max revisions reached. Proceeding to Evolution Proof. ---")
            return "evolution_proof"

    workflow.add_conditional_edges(
        "evaluation",
        should_revise,
        {
            "parallel_ideation": "parallel_ideation",
            "evolution_proof": "evolution_proof"
        }
    )
    workflow.add_edge("evolution_proof", END)
    
    app = workflow.compile()
    
    return app
