from typing import TypedDict, List

class PlannerState(TypedDict):
    """CD 플래너 에이전트 V2의 상태를 관리하는 스키마"""
    
    # User Input
    brief: str
    designer_feedback: str
    
    # Structured Brief Fields (V3)
    project_name: str
    target_audience: str
    goal: str
    tone_and_manner: str
    additional_context: str
    
    # Hook Strategy Fields (V3)
    selected_hook_strategy: str
    hook_reasoning: str
    
    # Research Phase
    web_context: str
    search_queries: List[str]
    research_data: str
    
    # Analysis Phase (V2: 마이크로 트라이브 분석)
    micro_tribe_analysis: str
    
    # Insight Phase (V2: 컬처럴 텐션 도출)
    cultural_tensions: str
    blueprint: str
    
    # Idea Phase (V2: 애자일 가설 및 마이크로 모먼츠 여정)
    agile_ideas: str
    
    # Performance Marketing Phase (V3.1)
    performance_data: str
    
    # Report Phase (V2.5: 20페이지 분할 생성)
    report_sec1: str
    report_sec2: str
    report_sec3: str
    final_report: str
    qa_feedback: str
    
    # PPT Code Phase (V3.0: PPT 변환용 코드 파싱)
    ppt_code: str
    
    # Evaluation Phase (V3.2: 심사위원 에이전트 퀄리티 검수)
    evaluation_report: str
