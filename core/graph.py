from langgraph.graph import StateGraph, END
from core.state import PlannerState
from core.nodes import web_search_node, parallel_ideation_node, synthesize_node, hook_strategy_node, parallel_report_node, report_merge_node, qa_judge_node, ppt_code_node, evaluation_node

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
    
    workflow.set_entry_point("web_search")
    workflow.add_edge("web_search", "parallel_ideation")
    workflow.add_edge("parallel_ideation", "synthesize")
    workflow.add_edge("synthesize", "hook_strategy")
    workflow.add_edge("hook_strategy", "parallel_report")
    workflow.add_edge("parallel_report", "report_merge")
    workflow.add_edge("report_merge", "qa_judge")
    workflow.add_edge("qa_judge", "ppt_code")
    workflow.add_edge("ppt_code", "evaluation")
    workflow.add_edge("evaluation", END)
    
    app = workflow.compile()
    
    return app
