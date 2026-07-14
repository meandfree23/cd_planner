import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults

def fetch_daily_trend_report() -> str:
    """
    Tavily를 통해 최신 글로벌 마케팅/예술 트렌드를 스캔하고, 
    LLM을 통해 [현상-본질-적용] 형태의 마크다운 리포트를 생성합니다.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    search_tool = TavilySearchResults(max_results=5)
    
    # 1. 최신 정보 수집 (Marketing & Art)
    marketing_query = "latest creative global marketing campaigns case study 2024"
    art_query = "latest contemporary art interactive installations exhibitions 2024"
    
    marketing_results = search_tool.invoke({"query": marketing_query})
    art_results = search_tool.invoke({"query": art_query})
    
    search_context = f"=== Marketing Search Results ===\n{marketing_results}\n\n=== Art Search Results ===\n{art_results}"
    
    # 2. LLM 분석 프롬프트
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 전 세계의 트렌드를 꿰뚫어보는 최고 권위의 시니어 크리에이티브 디렉터이자 큐레이터입니다.
주어진 최신 글로벌 검색 결과를 바탕으로, 가장 파괴적이고 영감을 주는 **마케팅 사례 1개**와 **예술 사례 1개**를 엄선하여 분석 리포트를 작성하세요.

[분석 및 출력 가이드 (마크다운 포맷)]
# 📰 오늘의 트렌드 & 아트 인사이트

오늘의 발굴 날짜: {date}

## 🔥 Global Marketing Case: [선정된 캠페인 이름]
- **현상 (What)**: 이 캠페인이 어떤 내용이며, 어떤 방식으로 사람들의 시선을 끌었는가?
- **본질 (Why)**: 이것이 타겟 소비자의 어떤 텐션(Tension)과 본성을 자극하여 성공했는가?
- **실무 적용 (How)**: 이 캠페인의 핵심 아이디어를 우리의 일상적인 기획/브랜딩 실무에 어떻게 차용할 수 있는가?

## 🎨 Contemporary Art Case: [선정된 예술 작품/전시 이름]
- **현상 (What)**: 어떤 작품/전시인가? 매체나 시각적 특성은 무엇인가?
- **본질 (Why)**: 이 작품이 우리 사회나 대중에게 던지는 미학적, 철학적 메시지는 무엇인가?
- **실무 적용 (How)**: 이 예술적 터치나 철학을 마케팅의 '경험(Experience)'이나 '톤앤매너'로 변환한다면 어떻게 써먹을 수 있는가?

## 💡 통합 인사이트 (The One Thing)
- 오늘 발견한 두 사례(마케팅과 예술)를 관통하는 단 하나의 거대한 시대적 흐름이나 인사이트는 무엇인가?

존댓말로 격식 있고 날카로운 카리스마를 담아, 한국어로 작성해주세요."""),
        ("user", "검색된 데이터:\n{search_context}")
    ])
    
    today_str = time.strftime("%Y년 %m월 %d일")
    response = llm.invoke(prompt.format_messages(date=today_str, search_context=search_context))
    report_content = response.content
    
    # 3. 폴더 및 파일 저장
    if not os.path.exists("trends"):
        os.makedirs("trends")
        
    filename = f"trends/{time.strftime('%Y-%m-%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return report_content

def load_trend_report(date_str: str) -> str:
    """특정 날짜의 리포트를 로드합니다. YYYY-MM-DD 형식"""
    filepath = f"trends/{date_str}.md"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return None

def get_all_trend_dates() -> list:
    """저장된 모든 트렌드 리포트의 날짜 목록을 반환합니다."""
    if not os.path.exists("trends"):
        return []
    files = [f for f in os.listdir("trends") if f.endswith(".md")]
    dates = sorted([f.replace(".md", "") for f in files], reverse=True)
    return dates
