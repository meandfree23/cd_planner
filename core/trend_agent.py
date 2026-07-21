import os
import time
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from tavily import TavilyClient

class TrendReport(BaseModel):
    marketing_brand: str = Field(description="마케팅 사례의 브랜드명 (특수기호 없이 깔끔하게)")
    marketing_what: str = Field(description="캠페인의 구체적 실행 내용 (80% 비중, 팩트 중심)")
    marketing_why: str = Field(description="캠페인의 핵심 인사이트 (10% 비중, 타겟의 텐션 자극 포인트)")
    marketing_how: str = Field(description="실무 적용 포인트 (10% 비중)")
    marketing_references: list[str] = Field(description="추가 파악을 위한 기사, 구글, 유튜브 링크 (URL만 3개 이내)")
    
    art_name: str = Field(description="예술 작품이나 전시명 (특수기호 없이 깔끔하게)")
    art_what: str = Field(description="전시의 구체적 실행 내용 (80% 비중, 팩트 중심)")
    art_why: str = Field(description="전시의 핵심 철학 (10% 비중)")
    art_how: str = Field(description="실무 적용 포인트 (10% 비중)")
    art_references: list[str] = Field(description="추가 파악을 위한 원문, 구글, 유튜브 링크 (URL만 3개 이내)")
    
    integration_insight: str = Field(description="두 사례를 관통하는 단 하나의 거대한 시대적 흐름이나 인사이트 (2~3문장)")
    image_search_keyword: str = Field(description="선정된 마케팅 캠페인의 대표 시각 이미지를 찾기 위한 3~5단어의 정확한 구글 이미지 검색 영문 키워드")


def extract_zeitgeist(llm) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 시대의 흐름을 읽는 문화 철학자이자 트렌드 분석가입니다. 2026년 현재 전 세계를 관통하는 단 하나의 거대한 시대정신(Zeitgeist)을 영문 키워드로 3~5단어 내외로 도출하세요. (예: AI-Human Emotional Symbiosis, Post-truth Authenticity, Hyper-Personalized Reality 등). 부가 설명 없이 오직 영문 키워드만 정확하게 출력하세요.")
    ])
    response = llm.invoke(prompt.format_messages())
    return response.content.strip()

def fetch_daily_trend_report() -> str:
    """
    Tavily를 통해 최신 글로벌 마케팅/예술 트렌드를 스캔하고, 
    LLM을 통해 Structured JSON 형태의 리포트를 생성하여 저장합니다.
    (기존 리턴값이 마크다운 문자열이었으나, 이제 JSON 덤프 문자열을 반환)
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, max_retries=15)
    structured_llm = llm.with_structured_output(TrendReport)
    tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    
    # 1. 시대정신(Zeitgeist) 도출
    zeitgeist = extract_zeitgeist(llm)
    
    # 2. 시대정신 기반 타겟 검색
    marketing_query = f"latest 2026 {zeitgeist} brand marketing campaign case study"
    art_query = f"latest 2026 {zeitgeist} contemporary art new perspective exhibition"
    
    try:
        m_resp = tavily.search(query=marketing_query, include_images=False, max_results=5)
        a_resp = tavily.search(query=art_query, include_images=False, max_results=5)
        marketing_results = str(m_resp.get("results", []))
        art_results = str(a_resp.get("results", []))
    except Exception as e:
        marketing_results = f"Search Failed: {str(e)}"
        art_results = f"Search Failed: {str(e)}"
    
    search_context = f"=== Marketing Search Results ({zeitgeist}) ===\n{marketing_results}\n\n=== Art Search Results ({zeitgeist}) ===\n{art_results}"
    
    # 3. LLM 분석 프롬프트
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 전 세계의 트렌드를 꿰뚫어보는 최고 권위의 시니어 크리에이티브 디렉터이자 큐레이터입니다.
주어진 최신 글로벌 검색 결과를 바탕으로, 제시된 **시대정신(Zeitgeist)**과 완벽히 공명하는 가장 파괴적이고 영감을 주는 **마케팅 사례 1개**와 **예술 사례 1개**를 엄선하여 완벽한 데이터를 추출하세요.

[선정 최우선 원칙]
1. 반드시 2026년 최신 사례를 우선적으로 발굴하세요. (정 없다면 과거 사례 응용)
2. 예술 분야는 새로운 매체, 파격적인 시도에 중점을 두세요.
3. 본문 작성 비율 원칙: 구체적인 팩트와 실행 내용(What) 80%, 핵심 인사이트(Why/How) 20%의 비중을 엄격히 지키세요. 뜬구름 잡는 철학적 수사보다 "실제로 어떤 매체를 통해 어떤 비주얼과 카피로 소통했는지" 아주 구체적인 실행 디테일을 상세히 기술해야 합니다."""),
        ("user", "검색된 데이터:\n{search_context}")
    ])
    
    today_str = time.strftime("%Y년 %m월 %d일")
    chain = prompt | structured_llm
    result: TrendReport = chain.invoke({"zeitgeist": zeitgeist, "search_context": search_context})
    
    # 4. 정밀 타겟팅 이미지 검색
    rep_image_url = ""
    if result.image_search_keyword:
        try:
            img_resp = tavily.search(query=result.image_search_keyword, include_images=True, max_results=1)
            imgs = img_resp.get("images", [])
            if imgs:
                rep_image_url = imgs[0]
        except:
            pass
            
    if not rep_image_url:
        rep_image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop"
        
    final_data = {
        "format_version": 2,
        "date": today_str,
        "zeitgeist": zeitgeist,
        "image_url": rep_image_url,
        "report": result.model_dump()
    }
    
    # 5. 폴더 및 파일 저장
    if not os.path.exists("trends"):
        os.makedirs("trends")
        
    file_id = time.strftime('%Y-%m-%d_%H%M%S')
    filename = f"trends/{file_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    return json.dumps(final_data, ensure_ascii=False)

def load_trend_report(file_id: str):
    """특정 파일 ID의 리포트를 로드합니다. JSON이 우선, 그 다음 MD를 찾습니다."""
    json_path = f"trends/{file_id}.json"
    md_path = f"trends/{file_id}.md"
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def delete_trend_report(file_id: str) -> bool:
    """특정 파일 ID의 리포트를 삭제합니다."""
    json_path = f"trends/{file_id}.json"
    md_path = f"trends/{file_id}.md"
    
    deleted = False
    if os.path.exists(json_path):
        os.remove(json_path)
        deleted = True
    if os.path.exists(md_path):
        os.remove(md_path)
        deleted = True
    return deleted

def get_all_trend_info() -> list:
    """저장된 모든 트렌드 리포트의 ID와 제목 목록을 반환합니다."""
    if not os.path.exists("trends"):
        return []
    files = [f for f in os.listdir("trends") if f.endswith(".md") or f.endswith(".json")]
    
    results = []
    processed_ids = set()
    
    for f in files:
        file_id = f.replace(".md", "").replace(".json", "")
        if file_id in processed_ids:
            continue
        processed_ids.add(file_id)
        
        date_str = file_id.split("_")[0] if "_" in file_id else file_id
        
        json_path = os.path.join("trends", f"{file_id}.json")
        md_path = os.path.join("trends", f"{file_id}.md")
        
        title = "제목 없음"
        image_url = ""
        
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            title = f"{data['report']['marketing_brand']} & {data['report']['art_name']}"
            image_url = data.get("image_url", "")
        elif os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as file:
                for line in file:
                    if not image_url and line.startswith("!["):
                        img_match = re.search(r'\!\[.*?\]\((.*?)\)', line)
                        if img_match:
                            extracted = img_match.group(1).strip()
                            if extracted.startswith("http"):
                                image_url = extracted
                    if line.startswith("# 📰 "):
                        title = line.replace("# 📰 ", "").strip().replace("[", "").replace("]", "")
                    elif line.startswith("# "):
                        if title == "제목 없음":
                            title = line.replace("# ", "").strip().replace("[", "").replace("]", "")
                            
            if not image_url and title != "제목 없음" and os.environ.get("TAVILY_API_KEY"):
                try:
                    from tavily import TavilyClient
                    tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
                    resp = tavily.search(query=title, include_images=True, max_results=1)
                    imgs = resp.get("images", [])
                    if imgs:
                        image_url = imgs[0]
                        with open(md_path, "r", encoding="utf-8") as file_read:
                            content = file_read.read()
                        with open(md_path, "w", encoding="utf-8") as file_write:
                            file_write.write(f"![대표 이미지]({image_url})\n\n" + content)
                except Exception:
                    pass
                    
        if not image_url or not image_url.startswith("http"):
            image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop"
            
        display_str = f"{date_str}: {title}"
        if len(display_str) > 40:
            display_str = display_str[:37] + "..."
            
        results.append({"file_id": file_id, "date_str": date_str, "display": display_str, "image_url": image_url})
    
    results = sorted(results, key=lambda x: x["file_id"], reverse=True)
    return results

def rewrite_all_reports_content() -> int:
    """기존 MD 리포트들을 읽어 새로운 Structured JSON 폼으로 완전히 개조하고 기존 파일을 삭제합니다."""
    if not os.path.exists("trends"):
        return 0
        
    count = 0
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        return 0
        
    tavily = TavilyClient(api_key=tavily_key)
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, max_retries=15)
    structured_llm = llm.with_structured_output(TrendReport)
    
    files = [f for f in os.listdir("trends") if f.endswith(".md")]
    
    for f in files:
        filepath = os.path.join("trends", f)
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            
        # 1. 과거 MD 구조에서 대략적인 정보 추출
        m_match = re.search(r'## 🔥 Global Marketing Case:\s*(.*)', content)
        a_match = re.search(r'## 🎨 Contemporary Art Case:\s*(.*)', content)
        z_match = re.search(r'오늘의 시대정신:\s*\*\*(.*?)\*\*', content)
        
        m_name = m_match.group(1).replace("[", "").replace("]", "").strip() if m_match else ""
        a_name = a_match.group(1).replace("[", "").replace("]", "").strip() if a_match else ""
        zeitgeist = z_match.group(1).strip() if z_match else "Cultural Evolution"
        
        if not m_name and not a_name:
            continue
            
        # 2. 정밀 검색 (새로운 팩트 발굴)
        m_query = f"{m_name} brand marketing campaign detailed case study"
        a_query = f"{a_name} contemporary art exhibition detailed review"
        
        try:
            m_resp = tavily.search(query=m_query, include_images=False, max_results=3)
            a_resp = tavily.search(query=a_query, include_images=False, max_results=3)
            marketing_results = str(m_resp.get("results", []))
            art_results = str(a_resp.get("results", []))
        except Exception:
            continue
            
        search_context = f"=== Marketing Search Results ===\n{marketing_results}\n\n=== Art Search Results ===\n{art_results}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 시니어 디렉터입니다. 검색 결과를 바탕으로 기존 리포트를 완벽하게 재작성하세요.
마케팅 타겟: {m_name}
예술 타겟: {a_name}
원칙: 구체적인 팩트와 실행 내용(What) 80%, 인사이트(Why/How) 20%의 비중 엄수. 뜬구름 잡는 표현 배제."""),
            ("user", "검색 데이터:\n{search_context}")
        ])
        
        try:
            chain = prompt | structured_llm
            result: TrendReport = chain.invoke({"m_name": m_name, "a_name": a_name, "search_context": search_context})
        except Exception:
            continue
            
        # 4. 이미지 갱신
        rep_image_url = ""
        if result.image_search_keyword:
            try:
                img_resp = tavily.search(query=result.image_search_keyword, include_images=True, max_results=1)
                imgs = img_resp.get("images", [])
                if imgs: rep_image_url = imgs[0]
            except Exception: pass
            
        if not rep_image_url:
            rep_image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop"
            
        file_id = f.replace(".md", "")
        date_str = file_id.split("_")[0] if "_" in file_id else time.strftime("%Y-%m-%d")
        
        final_data = {
            "format_version": 2,
            "date": date_str,
            "zeitgeist": zeitgeist,
            "image_url": rep_image_url,
            "report": result.model_dump()
        }
        
        with open(f"trends/{file_id}.json", "w", encoding="utf-8") as file_write:
            json.dump(final_data, file_write, ensure_ascii=False, indent=2)
            
        # 성공하면 구형 MD 파일 완전 삭제!
        os.remove(filepath)
        count += 1
        
    return count
