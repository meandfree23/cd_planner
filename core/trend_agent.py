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
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, max_retries=15)
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
# 📰 [브랜드명] 15자 이내의 아주 간결한 인사이트 요약

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
    
    # 3. 폴더 및 파일 저장 (누락 없이 누적하기 위해 타임스탬프 추가)
    if not os.path.exists("trends"):
        os.makedirs("trends")
        
    file_id = time.strftime('%Y-%m-%d_%H%M%S')
    filename = f"trends/{file_id}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return report_content

def load_trend_report(file_id: str) -> str:
    """특정 파일 ID의 리포트를 로드합니다."""
    filepath = f"trends/{file_id}.md"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return None

def delete_trend_report(file_id: str) -> bool:
    """특정 파일 ID의 리포트를 삭제합니다."""
    filepath = f"trends/{file_id}.md"
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

def get_all_trend_info() -> list:
    """저장된 모든 트렌드 리포트의 ID와 제목 목록을 반환합니다."""
    if not os.path.exists("trends"):
        return []
    files = [f for f in os.listdir("trends") if f.endswith(".md")]
    
    results = []
    for f in files:
        file_id = f.replace(".md", "")
        # 파일명에서 날짜 추출 (예: 2024-07-14_123456 -> 2024-07-14)
        date_str = file_id.split("_")[0] if "_" in file_id else file_id
        
        filepath = os.path.join("trends", f)
        title = "제목 없음"
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("# 📰 "):
                    title = line.replace("# 📰 ", "").strip()
                    break
                elif line.startswith("# "):
                    title = line.replace("# ", "").strip()
                    break
        
        # UI에 노출될 간결한 문자열
        display_str = f"{date_str}: {title}"
        if len(display_str) > 40:
            display_str = display_str[:37] + "..."
            
        results.append({"file_id": file_id, "date_str": date_str, "display": display_str})
    
    # 최신순 정렬 (file_id에 시간이 포함되어 있으므로 file_id 역순 정렬이 최신순임)
    results = sorted(results, key=lambda x: x["file_id"], reverse=True)
    return results
