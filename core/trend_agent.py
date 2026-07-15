import os
import time
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient

def extract_zeitgeist(llm) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 시대의 흐름을 읽는 문화 철학자이자 트렌드 분석가입니다. 2026년 현재 전 세계를 관통하는 단 하나의 거대한 시대정신(Zeitgeist)을 영문 키워드로 3~5단어 내외로 도출하세요. (예: AI-Human Emotional Symbiosis, Post-truth Authenticity, Hyper-Personalized Reality 등). 부가 설명 없이 오직 영문 키워드만 정확하게 출력하세요.")
    ])
    response = llm.invoke(prompt.format_messages())
    return response.content.strip()

def fetch_daily_trend_report() -> str:
    """
    Tavily를 통해 최신 글로벌 마케팅/예술 트렌드를 스캔하고, 
    LLM을 통해 [현상-본질-적용] 형태의 마크다운 리포트를 생성합니다.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, max_retries=15)
    tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    
    # 1. 시대정신(Zeitgeist) 도출
    zeitgeist = extract_zeitgeist(llm)
    
    # 2. 시대정신 기반 타겟 검색 및 이미지 추출
    marketing_query = f"latest 2026 {zeitgeist} brand marketing campaign case study"
    art_query = f"latest 2026 {zeitgeist} contemporary art new perspective exhibition"
    
    try:
        m_resp = tavily.search(query=marketing_query, include_images=True, max_results=5)
        a_resp = tavily.search(query=art_query, include_images=True, max_results=5)
        
        m_images = m_resp.get("images", [])
        a_images = a_resp.get("images", [])
        
        marketing_results = str(m_resp.get("results", []))
        art_results = str(a_resp.get("results", []))
        
        rep_image_url = m_images[0] if m_images else (a_images[0] if a_images else "")
    except Exception as e:
        marketing_results = f"Search Failed: {str(e)}"
        art_results = f"Search Failed: {str(e)}"
        rep_image_url = ""
    
    search_context = f"=== Marketing Search Results ({zeitgeist}) ===\n{marketing_results}\n\n=== Art Search Results ({zeitgeist}) ===\n{art_results}"
    image_md = f"![대표 이미지]({rep_image_url})\n\n" if rep_image_url else ""
    
    # 3. LLM 분석 프롬프트
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 전 세계의 트렌드를 꿰뚫어보는 최고 권위의 시니어 크리에이티브 디렉터이자 큐레이터입니다.
주어진 최신 글로벌 검색 결과를 바탕으로, 제시된 **시대정신(Zeitgeist)**과 완벽히 공명하는 가장 파괴적이고 영감을 주는 **마케팅 사례 1개**와 **예술 사례 1개**를 엄선하여 분석 리포트를 작성하세요.

[선정 최우선 원칙]
1. 반드시 2026년 최신 사례를 우선적으로 발굴하세요. 검색 결과에 적합한 2026년 사례가 도저히 없다면, 해당 시대정신과 가장 완벽하게 부합하는 과거 사례를 대신 선정하여 응용 가능성을 제시하세요.
2. 예술(Art) 분야의 경우, 뻔한 전통적 접근보다는 새로운 매체, 새로운 시선, 파격적인 시도에 중점을 두어 신선한 관점을 제공하세요.
3. **본문 작성 비율 원칙: 구체적인 팩트와 실행 내용(What) 80%, 핵심 인사이트(Why/How) 20%**의 비중을 엄격히 지키세요. 뜬구름 잡는 철학적 수사보다 "실제로 어떤 매체를 통해 어떤 비주얼과 카피, 어떤 기술로 대중과 소통했는지" 아주 구체적인 실행 디테일을 상세하게 서술해야 합니다.

[분석 및 출력 가이드 (마크다운 포맷)]
# 📰 [선정된 브랜드명 & 예술가명]: [어떤 파격적인 시도를 했는지 '구체적인 사실' 위주로 20자 이내 요약. "시대적 진화", "혁신적 감각" 등 뜬구름 잡는 추상적 표현 절대 금지]

오늘의 발굴 날짜: {date}
오늘의 시대정신: **{zeitgeist}**

## 🔥 Global Marketing Case: [선정된 캠페인 이름]
- **구체적 실행 내용 (What - 80% 비중)**: 이 캠페인이 '실제로' 어떻게 집행되었는가? 어떤 매체, 어떤 비주얼, 어떤 이벤트와 카피를 사용했는지 매우 상세하고 구체적인 팩트 위주로 생생하게 서술하세요.
- **핵심 인사이트 (Why - 10% 비중)**: 이것이 타겟 소비자의 어떤 텐션(Tension)을 정확히 찔렀는가?
- **실무 적용 포인트 (How - 10% 비중)**: 이 구체적인 아이디어를 우리의 실무에 당장 어떻게 차용할 수 있는가?
- **🔗 더 알아보기 (References)**: 이 사례의 실제 원문 기사 링크(검색 데이터 내 존재 시) 또는 추가 파악을 위한 [🔍 구글 검색](https://www.google.com/search?q=키워드) 및 [▶️ 유튜브 영상](https://www.youtube.com/results?search_query=키워드) 링크를 합쳐서 3개 내외로 반드시 첨부하세요.

## 🎨 Contemporary Art Case: [선정된 예술 작품/전시 이름]
- **구체적 전시 내용 (What - 80% 비중)**: 이 전시/작품은 '실제로' 어떻게 생겼으며 관객과 어떻게 상호작용하는가? 매체, 크기, 시각적 형태, 관람객의 동선 등을 눈에 그리듯 상세하고 구체적인 팩트 위주로 서술하세요.
- **핵심 철학 (Why - 10% 비중)**: 이 작품이 우리 사회에 던지는 날카로운 미학적 메시지는 무엇인가?
- **실무 적용 포인트 (How - 10% 비중)**: 이 구체적인 시각적/경험적 요소를 마케팅의 톤앤매너로 변환한다면 어떻게 써먹을 수 있는가?
- **🔗 더 알아보기 (References)**: 이 작품의 실제 원문 링크(검색 데이터 내 존재 시) 또는 추가 파악을 위한 [🔍 구글 검색](https://www.google.com/search?q=키워드) 및 [▶️ 유튜브 영상](https://www.youtube.com/results?search_query=키워드) 링크를 합쳐서 3개 내외로 반드시 첨부하세요.

## 💡 통합 인사이트 (The One Thing)
- 오늘 발견한 두 사례(마케팅과 예술)를 관통하는 단 하나의 거대한 시대적 흐름이나 인사이트는 무엇인가? (2~3문장 이내)

IMG_KEYWORD: [선정된 마케팅 캠페인의 가장 대표적인 시각적 이미지를 찾기 위한 3~5단어의 정확한 구글 이미지 검색어. 예: "Dove Real Cost Beauty campaign"]

존댓말로 격식 있고 날카로운 카리스마를 담아, 한국어로 작성해주세요."""),
        ("user", "검색된 데이터:\n{search_context}")
    ])
    
    today_str = time.strftime("%Y년 %m월 %d일")
    response = llm.invoke(prompt.format_messages(date=today_str, zeitgeist=zeitgeist, search_context=search_context))
    report_content = response.content
    
    # 이미지 키워드 파싱 및 정밀 검색
    rep_image_url = ""
    img_keyword = ""
    lines = report_content.split('\n')
    clean_lines = []
    for line in lines:
        if line.startswith("IMG_KEYWORD:"):
            img_keyword = line.replace("IMG_KEYWORD:", "").strip()
        else:
            clean_lines.append(line)
            
    report_content = '\n'.join(clean_lines).strip()
    
    if img_keyword:
        try:
            img_resp = tavily.search(query=img_keyword, include_images=True, max_results=1)
            imgs = img_resp.get("images", [])
            if imgs:
                rep_image_url = imgs[0]
        except Exception:
            pass
            
    if not rep_image_url:
        rep_image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop"
        
    report_content = f"![대표 이미지]({rep_image_url})\n\n" + report_content
    
    # 4. 폴더 및 파일 저장 (누락 없이 누적하기 위해 타임스탬프 추가)
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
        date_str = file_id.split("_")[0] if "_" in file_id else file_id
        
        filepath = os.path.join("trends", f)
        title = "제목 없음"
        image_url = ""
        
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                # 첫 번째 이미지 URL 추출
                if not image_url and line.startswith("!["):
                    img_match = re.search(r'\!\[.*?\]\((.*?)\)', line)
                    if img_match:
                        image_url = img_match.group(1)
                        
                if line.startswith("# 📰 "):
                    title = line.replace("# 📰 ", "").strip()
                elif line.startswith("# "):
                    if title == "제목 없음": # 이미 # 📰 로 찾았다면 건너뜀
                        title = line.replace("# ", "").strip()
        
        # 과거 리포트 중 이미지가 없는 경우, 즉석에서 검색하여 채워넣는 힐링 로직 (1회만 동작)
        if not image_url and title != "제목 없음" and os.environ.get("TAVILY_API_KEY"):
            try:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
                # 제목을 기반으로 이미지 검색
                resp = tavily.search(query=title, include_images=True, max_results=1)
                imgs = resp.get("images", [])
                if imgs:
                    image_url = imgs[0]
                    # 파일 최상단에 이미지 추가하여 영구 저장
                    with open(filepath, "r", encoding="utf-8") as file_read:
                        content = file_read.read()
                    with open(filepath, "w", encoding="utf-8") as file_write:
                        file_write.write(f"![대표 이미지]({image_url})\n\n" + content)
            except Exception:
                pass
        
        # 최후의 보루: 검색 실패시 멋진 기본 아트 이미지 제공
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop"
        
        display_str = f"{date_str}: {title}"
        if len(display_str) > 40:
            display_str = display_str[:37] + "..."
            
        results.append({"file_id": file_id, "date_str": date_str, "display": display_str, "image_url": image_url})
    
    results = sorted(results, key=lambda x: x["file_id"], reverse=True)
    return results

def regenerate_all_images() -> int:
    """모든 트렌드 리포트의 본문을 분석하여 이미지를 정밀하게 재구성합니다."""
    if not os.path.exists("trends"):
        return 0
        
    count = 0
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        return 0
        
    from tavily import TavilyClient
    tavily = TavilyClient(api_key=tavily_key)
    files = [f for f in os.listdir("trends") if f.endswith(".md")]
    
    import re
    for f in files:
        filepath = os.path.join("trends", f)
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            
        # 본문에서 캠페인명 추출
        campaign_match = re.search(r'## 🔥 Global Marketing Case:\s*(.*)', content)
        if not campaign_match:
            continue
            
        campaign_name = campaign_match.group(1).strip()
        # [ ] 등 불필요한 기호 제거
        campaign_name = re.sub(r'[\[\]]', '', campaign_name)
        search_query = f"{campaign_name} brand marketing campaign high quality"
        
        try:
            resp = tavily.search(query=search_query, include_images=True, max_results=1)
            imgs = resp.get("images", [])
            if imgs:
                new_image = imgs[0]
                # 기존 이미지 라인 삭제
                lines = content.split('\n')
                clean_lines = [line for line in lines if not line.startswith("![")]
                new_content = f"![대표 이미지]({new_image})\n\n" + '\n'.join(clean_lines).strip()
                
                with open(filepath, "w", encoding="utf-8") as file_write:
                    file_write.write(new_content)
                count += 1
        except Exception:
            continue
            
    return count
