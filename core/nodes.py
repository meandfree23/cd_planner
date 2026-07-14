import os
import json
import re
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from duckduckgo_search import DDGS

from core.state import PlannerState

import time
import random
import xml.etree.ElementTree as ET
import concurrent.futures
import google.generativeai as genai

_BEST_GEMINI_MODEL = None

def get_heidi_design_notes():
    import os
    notes_path = os.path.join(os.path.dirname(__file__), "heidi_design_study_notes.md")
    try:
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                notes = f.read().strip()
                if notes:
                    return f"\n[스터디된 PPT 레이아웃 디자인 원칙]:\n{notes}\n"
    except Exception as e:
        print(f"[SYSTEM] Heidi 스터디 노트 로드 오류: {e}")
    return ""

def get_gemini_llm():
    global _BEST_GEMINI_MODEL
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        if _BEST_GEMINI_MODEL is None:
            try:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                flash_models = [m.replace("models/", "") for m in available_models if "gemini-1.5-flash" in m.lower()]
                pro_models = [m.replace("models/", "") for m in available_models if "gemini" in m.lower() and "pro" in m.lower() and "vision" not in m.lower()]
                
                # 무료 티어에서 'limit: 0' 에러가 나는 무거운 모델 대신 가장 가볍고 쿼터가 많은 flash 우선 탐색
                if flash_models:
                    if "gemini-1.5-flash-latest" in flash_models:
                        _BEST_GEMINI_MODEL = "gemini-1.5-flash-latest"
                    else:
                        _BEST_GEMINI_MODEL = flash_models[0]
                elif pro_models:
                    if "gemini-1.5-pro-latest" in pro_models:
                        _BEST_GEMINI_MODEL = "gemini-1.5-pro-latest"
                    else:
                        _BEST_GEMINI_MODEL = pro_models[0]
                else:
                    _BEST_GEMINI_MODEL = "gemini-pro"
            except Exception as e:
                print(f"[SYSTEM] 모델 탐색 오류: {e}")
                _BEST_GEMINI_MODEL = "gemini-1.5-flash"
                
        # 무료 버전 15 RPM(분당 15회) 제한을 피하기 위한 강제 휴식 (안전하게 5초)
        time.sleep(5)
        print(f"Using cached model: {_BEST_GEMINI_MODEL}")
        return ChatGoogleGenerativeAI(model=_BEST_GEMINI_MODEL, temperature=0.7)
    
    # 최후의 안전장치
    return ChatOpenAI(model="gpt-4o", temperature=0.3)

def get_openai_llm():
    # 고품질 기획서 생성을 위해 메인 LLM을 GPT-4o 플래그십 모델로 롤백
    # Rate Limit (429) 에러 방지를 위해 자동 재시도 횟수 대폭 증가
    return ChatOpenAI(model="gpt-4o", temperature=0.3, max_retries=15)

def brand_asset_extractor_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] BRAND DEEP DIVE & SNS PERCEPTION ---")
    url = state.get("brand_url", "").strip()
    project_name = state.get("project_name", "")
    llm = get_openai_llm()

    scraped_text = ""
    if url:
        try:
            print(f"Crawling brand URL: {url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                scraped_text = " ".join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])])
                scraped_text = scraped_text[:5000] # 너무 길면 자름
        except Exception as e:
            print(f"URL Crawling Error: {e}")
            scraped_text = "크롤링 실패 또는 접근 불가."

    sns_text = ""
    try:
        if project_name:
            print(f"Scanning SNS for {project_name}")
            tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))
            search_res = tavily.search(query=f"{project_name} 후기 OR site:twitter.com {project_name} 반응 OR site:instiz.net {project_name}", search_depth="basic", max_results=3)
            sns_text = json.dumps(search_res.get('results', []), ensure_ascii=False)
    except Exception as e:
        print(f"Tavily Search Error: {e}")
        sns_text = "SNS 검색 실패."

    if not scraped_text and not sns_text:
        state["brand_assets"] = "입력된 브랜드 정보가 부족하여 분석을 생략합니다."
        return state

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 세계 최고의 '기업 본질 분석가 및 브랜드 전략가'입니다. 
제공된 기업 웹사이트 크롤링 데이터와 SNS 직관적 반응(Tavily 검색 결과)을 분석하여 아래 5가지 핵심 항목을 추출하세요. 
일반적이고 뻔한 이야기가 아닌, 해당 브랜드만이 가진 '고유의 오리지널리티(자산)'와 '현재 대중들의 날것의 평판'을 날카롭게 요약해야 합니다.

[추출 항목]
1. Brand Philosophy (브랜드 철학 및 본질)
2. Signature Assets (시그니처 메뉴/서비스/제품/고유 기술)
3. Core Differentiator (타사 대비 확실한 강점 및 베네핏)
4. Brand Tone & Manner (브랜드 고유의 분위기와 무드)
5. SNS Real-time Perception (소비자들의 직관적이고 날 것의 반응/평판)

분석 결과를 마크다운 형식으로 명확하고 임팩트 있게 작성하세요."""),
        ("user", "프로젝트명: {project_name}\n웹사이트 데이터: {scraped_text}\nSNS 반응 데이터: {sns_text}")
    ])
    
    chain = prompt | llm
    res = chain.invoke({
        "project_name": project_name,
        "scraped_text": scraped_text,
        "sns_text": sns_text
    })
    
    state["brand_assets"] = res.content
    return state

def web_search_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] WEB SEARCH (DUCKDUCKGO) ---")
    brief = state["brief"]
    llm = get_openai_llm()
    
    # 1. Extract 5 hacker queries
    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 최고급 트렌드 해커입니다. 브리프를 보고 가장 날 것의 밈과 텐션을 찾기 위한 구글 검색 쿼리 5개를 작성해주세요. 단순 검색이 아닌, X(트위터), 틱톡, 커뮤니티(인스티즈, 더쿠 등)의 실시간 반응을 긁어올 수 있도록 'site:twitter.com 키워드', 'site:tiktok.com/tag 키워드', 'site:instiz.net 키워드' 등의 해커 서치 연산자를 극단적으로 활용하세요. 리스트 형태의 JSON으로 반환해야 합니다. 예시: [\"site:twitter.com 브랜드 반응\", \"site:tiktok.com/tag 브랜드\", \"키워드 트렌드\"]"),
        ("user", "{brief}")
    ])
    
    chain = query_prompt | llm
    response = chain.invoke({"brief": brief})
    
    try:
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if match:
            queries = json.loads(match.group(0))
        else:
            raise ValueError("JSON 배열을 찾을 수 없습니다.")
    except Exception as e:
        print(f"JSON Parsing Error: {e}")
        queries = [f"{brief} 최신 뉴스", f"{brief} 여론조사", f"{brief} 이슈"]
        
    def fetch_up_folder_trends():
        import os
        sources_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sources.json")
        trends = []
        if not os.path.exists(sources_path):
            return ""
        try:
            with open(sources_path, "r", encoding="utf-8") as f:
                sources = json.load(f)
        except:
            return ""
        sampled_sources = random.sample(sources, min(3, len(sources)))
        trends.append("=== [최신 디자인/마케팅 북마크 ('up' 폴더) 트렌드] ===")
        for s in sampled_sources:
            url = s.get("url")
            name = s.get("name")
            if not url: continue
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    root = ET.fromstring(res.content)
                    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                    for item in items[:2]:
                        title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title")
                        desc = item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary")
                        if desc:
                            desc = re.sub(r'<[^>]+>', '', desc)[:200]
                        trends.append(f"- [{name}] {title} : {desc}")
            except Exception as e:
                continue
        return "\n".join(trends)

    web_results = []
    bookmark_trends = fetch_up_folder_trends()
    if bookmark_trends:
        web_results.append(bookmark_trends)
    
    # URL 직접 스크래핑 로직 (브리프 내에 URL이 존재할 경우 해당 사이트 내용 직접 추출)
    urls_in_brief = re.findall(r'(https?://\S+)', brief)
    for url in urls_in_brief:
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator=' ', strip=True)
            # 글자가 너무 길면 앞부분 3000자만 잘라서 사용
            text_snippet = text[:3000]
            web_results.append(f"[직접 스크래핑된 사이트 데이터: {url}]\nContent: {text_snippet}")
        except Exception as e:
            print(f"URL Scraping Failed for {url}: {e}")
            web_results.append(f"[스크래핑 실패: {url}]\nError: {e}")

    try:
        with DDGS() as ddgs:
            for q in queries:
                results = ddgs.text(q, max_results=2)
                for r in results:
                    web_results.append(f"Title: {r.get('title')}\nBody: {r.get('body')}\nURL: {r.get('href')}")
    except Exception as e:
        print(f"DuckDuckGo Search Failed: {e}")
        web_results.append(f"웹 검색 실패: {e}")
        
    web_context = "\n\n".join(web_results)
    
    return {"web_context": web_context, "search_queries": queries}

def research_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] RESEARCH ---")
    brief = state["brief"]
    llm = get_openai_llm()
    
    # web_search_node에서 이미 쿼리를 뽑았으므로 재활용
    queries = state.get("search_queries", [])
    if not queries:
        query_prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 리서치 전문가입니다. 다음 브리프를 보고 타겟 소비자의 라이프스타일, 최근 커뮤니티 트렌드(마이크로 트라이브), 그리고 시장의 문제점(Tension)을 찾을 수 있는 구글 검색 쿼리 3개를 작성해주세요. 리스트 형태의 JSON으로 반환해야 합니다. 예시: [\"쿼리1\", \"쿼리2\", \"쿼리3\"]"),
            ("user", "{brief}")
        ])
        chain = query_prompt | llm
        response = chain.invoke({"brief": brief})
    
        try:
            content = response.content
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                queries = json.loads(match.group(0))
            else:
                raise ValueError("JSON 배열을 찾을 수 없습니다.")
        except Exception as e:
            print(f"JSON Parsing Error: {e}")
            queries = [f"{brief} 커뮤니티 반응", f"{brief} 라이프스타일 트렌드", f"{brief} 타겟 분석"]
    
    tavily_key = os.environ.get("TAVILY_API_KEY")
    research_results = []
    
    # 앞선 web_search_node 결과물 병합
    web_context = state.get("web_context", "")
    if web_context:
        research_results.append(f"[실시간 웹 검색 결과(DuckDuckGo)]\n{web_context}\n")
    
    if tavily_key and tavily_key != "your_tavily_api_key_here":
        tavily = TavilyClient(api_key=tavily_key)
        for q in queries:
            try:
                res = tavily.search(query=q, search_depth="advanced", max_results=3)
                for r in res.get('results', []):
                    research_results.append(f"Title: {r['title']}\nContent: {r['content']}")
            except Exception as e:
                research_results.append(f"Query: {q} - Search Failed: {e}")
    else:
        research_results.append("Tavily API Key가 설정되지 않아 실제 검색은 건너뛰었습니다. (가상 데이터 적용)")
        
    research_data = "\n\n".join(research_results)
    
    return {"search_queries": queries, "research_data": research_data}


def analysis_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] ANALYSIS (MICRO-TRIBE) ---")
    llm = get_openai_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 최신 트렌드를 꿰뚫어보는 마케팅 분석가입니다. 주어진 브리프와 리서치 데이터를 바탕으로 타겟을 뭉뚱그려 분석하지 말고, 특정한 관심사나 취향으로 묶인 **'마이크로 트라이브(Micro-Tribe)' 2~3가지**로 세분화하여 분석해주세요. \n[분석의 절대 원칙]: 절대 '정보가 부족하다'거나 '추가 정보가 필요하다'고 대답하지 마세요. 데이터가 생소하거나 부족하다면, 파편적인 팩트들을 교차 검증하여 반드시 **명확한 인과관계(Reason Why)가 존재하는 논리적 연역/귀납 추론**을 도출해내세요. 뜬구름 잡는 추상적 가설은 배제하고, 분석과 근거에 뼈대를 둔 단단한 논리를 구축하세요."),
        ("user", "브리프: {brief}\n\n리서치 데이터:\n{research_data}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"brief": state["brief"], "research_data": state.get("research_data", "")})
    
    return {"micro_tribe_analysis": response.content}


def insight_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] INSIGHT (CULTURAL TENSION) ---")
    llm = get_openai_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 날카로운 전략 플래너입니다. 앞서 분석한 마이크로 트라이브들이 현재 겪고 있는 **사회적/문화적 갈등(Cultural Tension)**을 찾아내세요. \n[분석의 절대 원칙]: 정보 부족을 핑계로 분석을 거절하지 마세요. 수많은 팩트 조각들을 논리적으로 연결하여 확실한 **인과관계(Reason Why)**가 증명된 텐션과 인사이트를 도출해야 합니다. 추상적이거나 허무맹랑한 상상력 대신, 우리 브랜드가 왜 해결사 역할을 쥐어야 하는지에 대한 냉철하고 논리적인 당위성을 제시하세요."),
        ("user", "브리프: {brief}\n\n마이크로 트라이브 분석:\n{micro_tribe_analysis}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"brief": state["brief"], "micro_tribe_analysis": state.get("micro_tribe_analysis", "")})
    
    return {"cultural_tensions": response.content}


def idea_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] IDEA (AGILE & MICRO-MOMENTS) ---")
    llm = get_openai_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 세계적인 크리에이티브 디렉터입니다. 앞서 도출된 '팩트 기반의 단단한 분석(Reason Why)'을 바탕으로, 소비자에게 가장 효율적이고 치명적으로 다가갈 수 있는 파격적이고 추상적인 크리에이티브 '애자일 가설' 3가지와 '마이크로 모먼츠' 전략을 폭발시키세요. 분석 단계에서의 엄격함을 벗고, 이 단계에서는 철저히 소비자를 유혹하기 위한 창의적이고 추상적인 아이디어에 집중하세요. 마크다운으로 정리하세요."),
        ("user", "브리프: {brief}\n\n트라이브 분석:\n{micro_tribe_analysis}\n\n텐션 및 인사이트:\n{cultural_tensions}")
    ])
    
    formatted_messages = prompt.format_messages(
        brief=state["brief"],
        micro_tribe_analysis=state["micro_tribe_analysis"],
        cultural_tensions=state["cultural_tensions"]
    )
    
    try:
        response = llm.invoke(formatted_messages)
    except Exception as e:
        print(f"[SYSTEM] ⚠️ Gemini 실제 호출 중 에러 발생 (쿼터 초과 등): {e}")
        print("[SYSTEM] 🔄 안전장치 발동: GPT-4o 우회하여 아이디어를 발상합니다.")
        fallback_llm = get_openai_llm()
        response = fallback_llm.invoke(formatted_messages)
        
    return {"agile_ideas": response.content}


def performance_marketing_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] PERFORMANCE MARKETING ---")
    llm = get_openai_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 데이터 기반의 최고 수준 퍼포먼스 마케터입니다. CD가 발상한 '애자일 가설'과 '타겟 분석'을 확인하고, 이를 어떻게 숫자로 검증하고 매체에 태울 수 있을지 퍼포먼스 마케팅 전략(예상 CPC/CTR 벤치마크, 미디어 믹스 효율, A/B 테스트 통계 설계 등)을 날카롭게 도출하세요."),
        ("user", "브리프: {brief}\n\n타겟 분석:\n{micro_tribe_analysis}\n\n크리에이티브 가설:\n{agile_ideas}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        brief=state["brief"],
        micro_tribe_analysis=state.get("micro_tribe_analysis", ""),
        agile_ideas=state.get("agile_ideas", "")
    ))
    return {"performance_data": response.content}


def report_sec1_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT SEC 1: 환경 분석 및 통계 ---")
    llm = get_openai_llm()
    heidi_notes = get_heidi_design_notes()
    
    brand_assets = state.get("brand_assets", "")
    blueprint = state.get("blueprint", "")
    brand_context = f"\n[🏢 기업 자산 및 기획의 핵심 전략 명제(Blueprint)]\n이 기획서는 뜬구름 잡는 일반론이 되어서는 안 됩니다. 아래의 기업 고유 자산과 CSO의 전략 명제를 반드시 뼈대로 삼아 작성하세요:\n{brand_assets}\n{blueprint}\n" if (brand_assets or blueprint) else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 총 30페이지 분량의 [심층 결과 분석 보고서] 중 전반부(약 10~12장)를 작성하는 최고 수준의 비즈니스 및 전략 컨설턴트입니다.

[절대 금지 사항 - 위반 시 실패]
1. "이 프레젠테이션은 기획팀, 마케팅팀, CD가 조율한 결과입니다" 또는 "우리는 A/B 테스트를 통해 검증했습니다"와 같은 [기획의 과정이나 방법론(메타 발언)]을 절대 언급하지 마세요. 방법론은 백그라운드에 감추고 오직 도출된 [구체적인 결과와 날카로운 분석]만 이야기하세요.
2. 겉핥기식의 요약된 문장을 쓰지 마세요.
3. [분석의 절대 원칙]: 절대 '추가 정보가 필요하다'며 작성을 포기하거나 거절하지 마세요. 데이터가 부족하더라도 수집된 최소한의 팩트들을 엮어, 명확한 인과관계(Reason Why)가 증명된 논리적 추론으로 내용을 당당하게 100% 완성하세요.

지금은 **[Part 1: 현상 분석 및 원인 규명 - HOOK & ATTENTION]** 파트입니다.
특히 도입부(Slide 1~3)는 다음의 심리학적 훅(Hook) 전략을 철저히 반영하여 카피와 논리를 강렬하게 각색하세요:
- 선택된 훅 전략: {hook_strategy}
- 훅 설계 의도: {hook_reasoning}

작성 규칙:
1. 타겟 분석과 기획의 논리적 뼈대가 부족하지 않도록, 이 파트에서만 **반드시 10장~12장 분량**으로 매우 밀도 있게 슬라이드를 확장해서 작성하세요. 다음 핵심 내용들이 충분히 세분화되어 슬라이드(## Slide X)로 전개되어야 합니다:
   - [브랜드/주제 소개 및 탄생 배경]
   - [기존 시장/경쟁 환경의 한계와 고질적 문제점]
   - [브랜드/제품만의 독보적 기술 또는 전략적 특장점]
   - [주요 성과, 파트너십 또는 초기 반응 지표]
   - [실질적인 소비자 혜택 및 효용 가치 지표]
   - [과거부터 현재까지의 시장 가치 변화 또는 트렌드 추이]
   - [최근 거시적 시장 동향과 브랜드의 현재 위치]
   - (위 내용을 바탕으로 각각 1~2장씩 슬라이드를 배정해 깊이를 파고드세요)
2. 각 슬라이드의 [PT 스크립트]는 대단히 길고, 풍부하고, 구체적인 논술형이어야 합니다. (슬라이드당 최소 300자 이상)
3. 수집된 데이터(리서치, 통계 수치)를 적극 활용하여, 대상 현상 이면에 숨겨진 '결정적 원인'을 심층적으로 파고드세요.
4. 최소 2개 이상의 슬라이드에는 현상을 직관적으로 증명하는 `mermaid` 차트 코드를 삽입하세요.

{heidi_notes}
{feedback_context}
{brand_context}"""),
        ("user", "브리프: {brief}\n\n분석 기반 데이터:\n{research_data}\n{performance_data}")
    ])
    
    feedback_context = f"\n[🎨 이전 PPT 디자이너(Report 에이전트)의 역방향 피드백 반영 사항]\n디자이너의 요청: {state['designer_feedback']}\n이번 기획서 작성 시, 위 디자이너의 피드백을 최우선으로 반영하여 글의 호흡이나 데이터 구조, 포맷을 유동적으로 진화시키세요.\n" if state.get("designer_feedback") else ""
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        feedback_context=feedback_context,
        brand_context=brand_context,
        brief=state["brief"],
        hook_strategy=state.get("selected_hook_strategy", "기본 훅 전략"),
        hook_reasoning=state.get("hook_reasoning", ""),
        research_data=state.get("research_data", ""),
        performance_data=state.get("performance_data", "")
    ))
    return {"report_sec1": response.content}


def report_sec2_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT SEC 2: 타겟 분석 및 전략 ---")
    llm = get_openai_llm()
    heidi_notes = get_heidi_design_notes()
    
    brand_assets = state.get("brand_assets", "")
    blueprint = state.get("blueprint", "")
    brand_context = f"\n[🏢 기업 자산 및 기획의 핵심 전략 명제(Blueprint)]\n이 기획서는 뜬구름 잡는 일반론이 되어서는 안 됩니다. 아래의 기업 고유 자산과 CSO의 전략 명제를 반드시 뼈대로 삼아 작성하세요:\n{brand_assets}\n{blueprint}\n" if (brand_assets or blueprint) else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 총 30페이지 분량의 [심층 결과 분석 보고서] 중 중반부(약 10~12장)를 작성하는 최고 수준의 타겟 전략 분석가이자 크리에이티브 디렉터입니다.

[절대 금지 사항 - 위반 시 실패]
1. "기획의 과정, 방법론, 분석 툴"에 대한 이야기는 일절 배제하세요. 오로지 도출된 분석의 [실질적 결과와 핵심 방향]에만 집중하세요.
2. 겉핥기식의 뻔한 설명을 배제하고, 독창적이고 심도 깊은 통찰력을 보여주세요.
3. [분석의 절대 원칙]: 절대 '추가 정보가 필요하다'며 작성을 포기하거나 거절하지 마세요. 데이터가 부족하더라도 수집된 최소한의 팩트들을 엮어, 명확한 인과관계(Reason Why)가 증명된 논리적 추론으로 내용을 당당하게 100% 완성하세요.

지금은 **[Part 2: 전략, 아이디어 및 미래 비전 - DEEP PERSUASION & IMPACT]** 파트입니다.
예술적 레퍼런스나 마케팅 KPI는 다른 파트에서 다루니 이곳에서는 작성하지 마세요.

작성 규칙:
1. 메인 기획의 뼈대가 부실해지지 않도록, 이 파트에서만 **반드시 10장~12장 분량**으로 슬라이드를 꽉 채워 작성하세요. 다음 핵심 내용들이 충분히 세분화되어 슬라이드(## Slide X)로 촘촘하게 전개되어야 합니다:
   - [주요 타겟 집단(마이크로 트라이브) 프로파일링 분석]
   - [타겟 집단이 겪고 있는 본질적인 미충족 요구(Unmet Needs)]
   - [시장과 타겟 사이에 존재하는 사회적/문화적 텐션(Tension) 해부]
   - [제안하는 핵심 아이디어 가설 및 크리에이티브 방향성 상세 전개 (최소 3장 이상 할당)]
   - [새로운 솔루션/제품 도입이 타겟 생태계에 미칠 즉각적 영향 및 단기 성장 로드맵]
   - [거시적 환경 변화(정책, 트렌드 등)에 따른 중장기 기회 요인 및 비즈니스 선순환(플라이휠)]
   - [글로벌/사회적 가치 창출(ESG) 및 궁극적 상생 비전]
2. 각 슬라이드의 [PT 스크립트]는 풍부한 사례와 근거를 들어 아주 상세하게 논술해야 합니다. (슬라이드당 최소 300자 이상)
3. 대상 타겟층(마이크로 트라이브)의 기저에 깔린 사회적/문화적 텐션(Tension)이나 미충족 요구(Unmet Needs)를 깊이 해부하고, 이것이 왜 발생하는지 비즈니스적/구조적 인과 관계를 증명하세요.
4. 타겟의 행동 여정이나 상호작용의 흐름을 시각화하는 `mermaid` 흐름도(graph TD) 코드를 최소 2개 삽입하세요.

{heidi_notes}
{brand_context}"""),
        ("user", "브리프: {brief}\n\n트라이브 및 텐션 데이터:\n{micro_tribe_analysis}\n{cultural_tensions}\n\n추가 데이터:\n{performance_data}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        brand_context=brand_context,
        brief=state["brief"],
        micro_tribe_analysis=state.get("micro_tribe_analysis", ""),
        cultural_tensions=state.get("cultural_tensions", ""),
        performance_data=state.get("performance_data", "")
    ))
    return {"report_sec2": response.content}


def report_sec3_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT SEC 3: 실행 계획 및 예산 ---")
    llm = get_openai_llm()
    heidi_notes = get_heidi_design_notes()
    
    brand_assets = state.get("brand_assets", "")
    blueprint = state.get("blueprint", "")
    brand_context = f"\n[🏢 기업 자산 및 기획의 핵심 전략 명제(Blueprint)]\n이 기획서는 뜬구름 잡는 일반론이 되어서는 안 됩니다. 아래의 기업 고유 자산과 CSO의 전략 명제를 반드시 뼈대로 삼아 작성하세요:\n{brand_assets}\n{blueprint}\n" if (brand_assets or blueprint) else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 총 30페이지 분량의 기획서 중 가장 후반부(25~30페이지 구간)를 장식하는 하이엔드 아트 디렉터입니다.

[절대 금지 사항 - 위반 시 실패]
1. 타겟 분석, 일반적인 마케팅 전략, 거시적 비전 등 코어 기획에 해당하는 내용은 앞선 파트에서 이미 20장 분량으로 서술되었으므로 절대 중복해서 작성하지 마세요.
2. 퍼포먼스 마케팅이나 KPI 수치 데이터도 작성하지 마세요 (별첨으로 처리됨).

지금은 **[Part 3: 예술적 승화 및 콘텐츠 예시 - ART & CONTENT REFERENCE]** 파트입니다.
앞서 도출된 기획안의 실행 단계를 한 차원 높일 수 있는 "콘텐츠 예시"와 "예술적 레퍼런스"만을 집중적으로 보여줍니다.

작성 규칙:
1. 오직 레퍼런스와 예시에만 집중하여 **딱 5장 분량**의 슬라이드로 작성하세요. (## Slide X 포맷 유지)
2. 각 슬라이드는 다음 중 하나의 예시를 깊게 다뤄야 합니다:
   - 시각적 레퍼런스 (특정 미학, 사진, 디자인 사조 적용 예시)
   - 과정 중심 레퍼런스 (독특한 팝업스토어, 오디오 도슨트 등 브랜드 경험 예시)
   - 컨셉추얼 레퍼런스 (현대무용, 문학, 시 등 추상적 개념을 브랜드 마케팅에 접목한 예시)
   - 파격적 콘텐츠/캠페인 기획 예시 (숏폼, 캠페인 필름 등)
3. 제시되는 5개의 예술적/콘텐츠적 예시가 앞선 코어 마케팅 논리와 **어떻게 뾰족하게 연결되는지** 명확한 인과성을 증명하세요.
3. 각 슬라이드의 [PT 스크립트]는 통계적 수치와 예술적 미학을 바탕으로 한, 가장 밀도 높고 통찰력 있는 장문의 논술(최소 300자 이상)이어야 합니다.
4. 미래 발전 마일스톤이나 예술적 상호작용 프로세스를 보여주는 `mermaid` 차트를 최소 2개 삽입하세요.

{heidi_notes}
{brand_context}"""),
        ("user", "브리프: {brief}\n\n기초 아이디어 가설 및 비전:\n{agile_ideas}\n\n예술적 레퍼런스(Artistic Layer):\n{artistic_references}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        brand_context=brand_context,
        brief=state["brief"],
        agile_ideas=state.get("agile_ideas", ""),
        artistic_references=state.get("artistic_references", "")
    ))
    return {"report_sec3": response.content}

def report_appendix_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT APPENDIX: 퍼포먼스 마케팅 별첨 ---")
    llm = get_openai_llm()
    heidi_notes = get_heidi_design_notes()
    
    brand_assets = state.get("brand_assets", "")
    blueprint = state.get("blueprint", "")
    brand_context = f"\n[🏢 기업 자산 및 기획의 핵심 전략 명제(Blueprint)]\n이 기획서는 뜬구름 잡는 일반론이 되어서는 안 됩니다. 아래의 기업 고유 자산과 CSO의 전략 명제를 반드시 뼈대로 삼아 작성하세요:\n{brand_assets}\n{blueprint}\n" if (brand_assets or blueprint) else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 [심층 결과 분석 보고서]의 마지막을 장식하는 최고 수준의 퍼포먼스 마케팅 디렉터입니다.

지금은 기획서의 맨 마지막 **[별첨(Appendix): 퍼포먼스 마케팅 및 매체/RFP 전략]** 파트입니다.
앞선 메인 기획서의 예술적이고 거시적인 비전을 해치지 않도록, 숫자가 중심이 되는 마케팅 전략만을 따로 빼서 전문적으로 정리합니다.

작성 규칙:
1. 슬라이드 제목은 '## Slide X' 대신 '## Appendix X: [제목]' 형식으로 작성하세요.
2. 분량은 자유롭되 최소 3~5장 이상의 Appendix 슬라이드를 구성하세요.
3. 반드시 포함되어야 할 내용:
   - 타겟별 매체 믹스(Media Mix) 및 도달 전략
   - 핵심 성과 지표(KPI, 예상 CPC/CTR) 및 데이터 검증 목표
   - RFP 대응, 예산 효율성, A/B 테스트 운영 계획
4. 각 슬라이드의 [PT 스크립트]는 실무적이고 구체적인 숫자를 바탕으로 최소 300자 이상 작성하세요.

{heidi_notes}
{brand_context}"""),
        ("user", "브리프: {brief}\n\n퍼포먼스 마케팅 전략 데이터:\n{performance_data}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        brand_context=brand_context,
        brief=state["brief"],
        performance_data=state.get("performance_data", "")
    ))
    return {"report_appendix": response.content}


def report_merge_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT MERGE ---")
    
    sec1 = state.get("report_sec1", "")
    sec2 = state.get("report_sec2", "")
    sec3 = state.get("report_sec3", "")
    appx = state.get("report_appendix", "")
    
    final_markdown = f"""# 📈 [심층 프레젠테이션] CD 플래닝 마스터 보고서

> 본 보고서는 통계 데이터와 시각화 차트를 포함한 프리젠테이션 대본 양식으로 작성되었습니다.

{sec1}

---

{sec2}

---

{sec3}

---

# 📑 [별첨] 퍼포먼스 마케팅 및 매체 전략 (Appendix)
{appx}
"""
    return {"final_report": final_markdown}

def qa_judge_node(state: PlannerState) -> PlannerState:
    """
    작성된 기획서(final_report)를 심사하여 개선점과 피드백을 도출하는 퀄리티 검수(QA) 에이전트.
    브리프를 분석하여 심사위원 페르소나를 자동 선택합니다.
    """
    print("--- [NODE] QA JUDGE (AUTO-PERSONA) ---")
    llm = get_openai_llm()
    brief = state["brief"]
    
    # 1. 페르소나 자동 판별
    persona_prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 라우팅 AI입니다. 브리프를 보고 다음 2가지 심사위원 중 하나를 선택해 번호(1 또는 2)만 대답하세요.\n1: 15년 차 보수적/논리적 시니어 심사위원 (B2B, 신뢰, 정보 전달 위주)\n2: 8년 차 트렌디/파격적 CD 심사위원 (팝업, 뷰티, 패션, F&B, MZ 타겟, 인스타그래머블)"),
        ("user", "브리프: {brief}")
    ])
    persona_decision = (persona_prompt | llm).invoke({"brief": brief}).content.strip()
    
    if "2" in persona_decision:
        print("[QA JUDGE] 🎧 트렌디한 8년 차 MZ CD 심사위원 출격!")
        judge_persona = """당신은 광고 대행사의 잘 나가는 8~10년 차 트렌디 크리에이티브 디렉터(Judge)입니다.
제출된 기획서를 검수하되, 젊은 감각과 트렌드(밈, 팝업, 숏폼, 팝컬처) 관점에서 무자비하고 날 것의 힙한 피드백을 주세요.

작성 규칙:
1. 칭찬은 아주 쿨하게 1줄로 끝내고, 아이디어가 너무 '올드'하거나 '뻔할 경우' 직설적이고 매운맛 코멘트로 지적하세요. (예: "요즘 누가 이런 걸 봅니까? 차라리 숏폼 챌린지로 비트세요.")
2. 실질적으로 힙(Hip)함을 한 스푼 얹기 위해 "반드시 추가/수정해야 할 구체적인 트렌디 액션 아이템 3가지"를 제안하세요.
3. 마크다운 형식으로 보기 좋게 정리해서 심사평을 작성하세요.
"""
    else:
        print("[QA JUDGE] 👔 논리적인 15년 차 시니어 심사위원 출격!")
        judge_persona = """당신은 수십 년 경력의 날카롭고 냉철한 '프리젠테이션 심사위원(QA 에이전트)'입니다.
제출된 전체 기획서 및 별첨(Appendix)을 꼼꼼히 평가하세요.

작성 규칙:
1. 칭찬은 1줄로 짧게 끝내고, 기획서의 논리적 비약, 설득력 부족, 타겟 텐션과의 연결성 부족 등 '약점(Weakness)'을 날카롭게 지적하세요.
2. 실질적으로 기획의 퀄리티를 높이기 위해 "작성자가 반드시 수정/보완해야 할 구체적인 액션 아이템 3가지"를 강력히 요구하세요.
3. 마크다운 형식으로 보기 좋게 정리해서 심사평을 작성하세요.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", judge_persona),
        ("user", "기획서 원문:\n{final_report}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        final_report=state.get("final_report", "")
    ))
    
    return {"qa_feedback": response.content}

def ppt_code_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] PPT CODE EXTRACTION ---")
    llm = get_openai_llm()
    heidi_notes = get_heidi_design_notes()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 마크다운 기획서를 특정 PPT 렌더링 엔진(auto-ot)이 읽을 수 있는 특수 텍스트 코드로 [100% 무손실 변환(Mapping)]하는 전문 코더입니다.

[절대 규칙 - 위반 시 렌더링이 실패함]:
1. 슬라이드 구분자는 반드시 "Slide X: [슬라이드 제목]" 형식을 사용하세요. 대문자 "SLIDE X"나 다른 대괄호 감싸기는 금지됩니다. (예: `Slide 1: [핵심 현상 분석]`)
2. 각 슬라이드는 반드시 아래의 태그들로 내용을 완벽하게 구성해야 합니다. 임의의 구조나 생략은 허용되지 않습니다.
   - `[카피]` 태그 바로 아래줄: 1단계 초강조 키워드 (10자 이내) 및 2단계 일반 강조 서브 (20자 이내) 문구
   - `[설명]` 태그 바로 아래줄: 3단계 본문 설명 (2줄 이내, 약 30자 내외로 핵심 정보를 알차고 밀도 있게 나열)
   - `[PT 스크립트]` 태그 바로 아래줄: 발표자가 읽을 상세한 설명 (최소 300자 이상, 기획서 원본의 데이터를 절대 요약하지 마세요)
3. 원본 기획서에 포함된 모든 분석 데이터, 통계 수치, 핵심 지표 등을 누락 없이 충실하게 적어 넣으세요.
4. **총 30장 내외의 슬라이드 분량(메인 코어기획 20~25장 + 예술적 예시 5장) 및 뒤따르는 Appendix(별첨)까지, 기획서 원문에 있는 모든 슬라이드(Slide 1 ~ Slide 30+ 및 Appendix)를 100% 하나도 빠짐없이 매핑하여 출력하세요.** 모델의 출력 토큰 한계에 도달하지 않도록 텍스트를 구조화하되, 슬라이드를 임의로 축소하지 마세요.

{heidi_notes}
{feedback_context}

반드시 마크다운 코드블록(```text ... ```) 안에 담아주세요.

출력 포맷 예시 (이 구조를 반복하여 모든 슬라이드와 Appendix를 완벽하게 구성하세요):
# [보고서를 관통하는 대주제 제목]

Slide 1: [브랜드/프로젝트 핵심 개요 및 존재 가치]
[카피]
새로운 시대의 문법을 제시하는 획기적 브랜드 철학
[설명]
- 타겟 소비자의 미충족 요구(Unmet Needs)를 완벽히 해결하는 솔루션
- 기존 경쟁 시장의 고질적 한계와 비효율을 타파하는 파괴적 혁신
[PT 스크립트]
이 슬라이드에서는 해당 브랜드 또는 프로젝트가 탄생하게 된 본질적인 배경과 시장 내 가치에 대해 설명합니다. 기존 산업 환경이 가진 낡은 관행이나 한계를 보완하기 위해 등장했으며, 고객에게 압도적인 편의성과 혁신적 가치를 제공합니다. 이를 통해 핵심 타겟 생태계의 판도를 바꾸고, 장기적인 시장 점유율 확대를 견인할 수 있습니다. (기획서 원문의 실제 상세 데이터와 수치를 300자 이상 풍부하게 반영)

Slide 2: [기존 시장/경쟁 환경의 한계와 구조적 문제점]
..."""),
        ("user", "전체 심층 분석 보고서 원문 (절대 요약하지 말고 태그에 분배할 것):\n{final_report}")
    ])
    
    feedback_context = f"\n[🎨 이전 PPT 디자이너(Report 에이전트)의 역방향 피드백 반영 사항]\n디자이너의 요청: {state['designer_feedback']}\n이번 PPT 코드 추출 시, 위 디자이너의 피드백을 최우선으로 반영하여 포맷과 데이터 구성을 알맞게 조정하세요.\n" if state.get("designer_feedback") else ""
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        feedback_context=feedback_context,
        final_report=state.get("final_report", "")
    ))
    
    code_content = response.content
    # 마크다운 텍스트 블록 안의 내용만 추출
    import re
    match = re.search(r'```(?:text)?(.*?)```', code_content, re.DOTALL)
    if match:
        code_content = match.group(1).strip()
    
    return {"ppt_code": code_content}

def evaluation_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] MULTI-JURY EVALUATION (다면 심사 위원회) ---")
    llm = get_openai_llm()
    brief = state["brief"]
    goal = state.get("goal", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 세계 최고 권위의 '칸 라이언즈(Cannes Lions) 급 다면 심사 위원회'입니다.
프로젝트 목표(Goal)에 따라 3인의 심사위원 가중치를 자동 조정하여 엄격하게 평가하세요.

[심사위원 3인 페르소나]
1. 🎨 칸 광고제 크리에이티브 심사위원장 (Art/Creative): 아이디어의 참신성, 타겟 텐션을 찌르는 파괴력 검증.
2. 📈 글로벌 퍼포먼스 마케팅 디렉터 (ROI/Data): 통계적 타당성, KPI 구체성, 예산 대비 전환율 논리 검증.
3. 🔥 Z세대 밈 & 트렌드 해커 (Era/Trend): 시대의 흐름, 바이럴 폭발력, SNS 생태계 및 문화적 적합성 검증.

[가중치 부여 가이드 (10점 만점 기준)]
목표(Goal)가 "{goal}" 입니다. 이 목표에 가장 결정적인 역할을 하는 심사위원의 비중을 높여서 평가를 진행하세요.

[출력 양식 (마크다운)]
# ⚖️ 다면 심사 위원회(Multi-Jury) 검수 보고서

## 1. 📊 종합 평가 및 심사 평점
- **종합 점수**: [점수] / 10 (가중치 합산 결과)
- **한 줄 심사평**: [세 심사위원의 의견을 종합한 촌철살인 한 줄 평]

## 2. 👩‍⚖️ 심사위원별 상세 피드백
### 🎨 크리에이티브 심사위원장 (비중: XX%)
- **강점**: [평가 내용]
- **⚠️ 치명적 약점 및 수정 지시**: [구체적 지적]

### 📈 퍼포먼스 마케팅 디렉터 (비중: XX%)
- **강점**: [평가 내용]
- **⚠️ 치명적 약점 및 수정 지시**: [구체적 지적]

### 🔥 Z세대 트렌드 해커 (비중: XX%)
- **강점**: [평가 내용]
- **⚠️ 치명적 약점 및 수정 지시**: [구체적 지적]

## 3. 🛠️ 다음 루프를 위한 최종 수정 명령 (Revise Requests)
- [시스템이 재작성 시 반드시 반영해야 할 구체적이고 명확한 행동 지침 3가지]

존댓말로 격식 있고 날카로운 카리스마를 담아 작성해주세요."""),
        ("user", "캠페인 브리프: {brief}\n\n최종 기획서 원문:\n{final_report}\n\nPPT 파싱 코드:\n{ppt_code}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        goal=goal,
        brief=brief,
        final_report=state.get("final_report", ""),
        ppt_code=state.get("ppt_code", "")
    ))
    
    current_revision = state.get("revision_count", 0)
    
    # 1회차(revision_count == 0)일 경우 초안을 보존
    v1_report = state.get("v1_report", "")
    if current_revision == 0:
        v1_report = state.get("final_report", "")
        
    return {
        "evaluation_report": response.content,
        "evaluation_feedback": response.content,
        "revision_count": current_revision + 1,
        "v1_report": v1_report
    }

def evolution_proof_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] EVOLUTION PROOF (진화 증명 에이전트) ---")
    llm = get_openai_llm()
    
    revision_count = state.get("revision_count", 0)
    # 만약 재작업(루프)이 한 번도 발생하지 않고 초안이 곧 최종안(점수 9점 이상 통과)이라면, 진화 증명 생략
    if revision_count <= 1:
        return {"evolution_proof": "✨ **[초안 통과]** 다면 심사 위원회의 엄격한 기준(9.0점 이상)을 단번에 통과하여, 별도의 재작성(진화) 없이 확정된 마스터피스입니다."}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 시스템의 투명성을 담당하는 '진화 증명(Evolution Proof) 에이전트'입니다.
AI가 '심사위원의 지적'을 받아들여 '초안(V1)'에서 '최종안'으로 넘어올 때, 겉치레가 아니라 **실제로 무엇이 어떻게 개선되었는지(Delta)**를 사용자에게 명백하게 증명해야 합니다.

[출력 양식 (마크다운)]
이 기획서는 다면 심사 위원회의 뼈아픈 지적을 수용하여 다음과 같이 진화했습니다.

## 1. 🔍 심사위원 지적 vs 최종안의 변화 (Delta)
- **지적 사항 A**: [퍼포먼스 마케팅 디렉터 등이 지적했던 내용 요약]
  - **✨ 진화된 결과**: [최종안의 어떤 슬라이드, 어떤 문장에 구체적인 수치/논리가 추가되었는지 팩트 위주로 증명]
- **지적 사항 B**: [트렌드 해커 등이 지적했던 내용 요약]
  - **✨ 진화된 결과**: [어떻게 개선되었는지 구체적으로 증명]

## 2. 💡 AI 자기 객관화 총평
- [이 자가 학습 루프를 통해 기획서의 방어율과 퀄리티가 어떻게 높아졌는지 2~3줄로 요약]"""),
        ("user", "다면 심사 위원회 지적사항:\n{feedback}\n\n초안(V1) 원문:\n{v1_report}\n\n최종안 원문:\n{final_report}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        feedback=state.get("evaluation_feedback", ""),
        v1_report=state.get("v1_report", ""),
        final_report=state.get("final_report", "")
    ))
    
    return {"evolution_proof": response.content}


# =====================================================================
# PHASE 4: PARALLEL MULTI-AGENT ARCHITECTURE
# =====================================================================

def parallel_ideation_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] HYBRID IDEATION (Research/Analysis -> Idea/Marketing) ---")
    brief = state["brief"]
    web_context = state.get("web_context", "")
    eval_feedback = state.get("evaluation_feedback", "")
    brand_assets = state.get("brand_assets", "")
    
    feedback_context = f"\n[🚨 자아비판 및 수정 지시]\n지난번 심사위원 검수에서 다음 뼈아픈 지적을 받았습니다. 이 피드백을 200% 수용하여 통계 수치와 구체적 벤치마크, 명확한 논리 구조를 덧붙여 기획을 전면 개편하세요:\n{eval_feedback}\n" if eval_feedback else ""
    
    brand_context = f"\n[🏢 기업 자산 및 SNS 반응 심층 분석]\n아래의 분석된 기업 자산을 최우선 뼈대로 삼아 모든 기획을 전개하세요. 일반적인 트렌드 분석에 그치지 말고, 이 브랜드만의 오리지널리티(메뉴/철학)와 SNS에서의 날것의 평판을 결합하여 이 브랜드'만' 할 수 있는 고유한 전략을 도출하세요:\n{brand_assets}\n" if brand_assets and "미입력" not in brand_assets and "부족" not in brand_assets else ""

    llm = get_openai_llm()
    
    def run_research():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 최고 수준의 리서처입니다. 주어진 브리프와 웹 검색 컨텍스트, 그리고 기업 자산을 바탕으로 타겟 소비자의 라이프스타일, 트렌드, 그리고 마이크로 트라이브(Micro-Tribe)를 3가지로 압축해 분석하세요.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**\n{feedback_context}\n{brand_context}"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context, "feedback_context": feedback_context, "brand_context": brand_context}).content

    def run_analysis():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 예리한 전략 분석가입니다. 주어진 브리프와 기업 자산을 보고 타겟 소비자들이 겪고 있는 핵심 갈등과 컬처럴 텐션(Cultural Tension)을 3가지 도출하세요. 인과관계가 명확해야 합니다.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**\n{feedback_context}\n{brand_context}"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context, "feedback_context": feedback_context, "brand_context": brand_context}).content

    # 1. First Phase: Research & Analysis (Parallel)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_res = executor.submit(run_research)
        f_ana = executor.submit(run_analysis)
        research_data = f_res.result()
        micro_tribe = f_ana.result()

    # 2. Second Phase: Ideation & Marketing (Parallel, strictly based on Phase 1 results)
    def run_idea():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 파격적인 크리에이티브 디렉터입니다. 브리프와 기업 자산, **앞서 분석된 타겟 텐션(Tension)**을 바탕으로 소비자를 유혹할 애자일 크리에이티브 가설(Agile Idea) 3가지를 도출하세요. **특히 컨텍스트 내에 '최신 디자인/마케팅 트렌드'가 있다면 아이디어에 강제로 결합시켜 매우 동시대적인 제안을 만드세요.** 반드시 앞선 전략가의 '텐션 분석'과 브랜드의 '자체 자산'을 본질적으로 해결/활용하는 아이디어여야 합니다.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**\n{feedback_context}\n{brand_context}"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}\n\n전략가의 타겟/텐션 분석:\n{analysis_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context, "analysis_context": micro_tribe, "feedback_context": feedback_context, "brand_context": brand_context}).content
        
    def run_marketing():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 퍼포먼스 마케터입니다. 브리프와 전략가의 '타겟/텐션 분석', 그리고 '기업 자산' 결과를 바탕으로, 이 타겟에게 도달하기 위한 핵심 매체 믹스, 예상 KPI(CPC/CTR), A/B 테스트 전략을 수립하세요.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**\n{feedback_context}\n{brand_context}"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}\n\n전략가의 타겟/텐션 분석:\n{analysis_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context, "analysis_context": micro_tribe, "feedback_context": feedback_context, "brand_context": brand_context}).content

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_ide = executor.submit(run_idea)
        f_mar = executor.submit(run_marketing)
        agile_ideas = f_ide.result()
        perf_data = f_mar.result()

    # 3. Third Phase: Art Director (Sequential, based on Idea & Marketing)
    def run_art_director():
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 구찌, 젠틀몬스터 등의 캠페인을 총괄했던 하이엔드 아트 디렉터입니다. 
마케터와 CD가 도출한 기획안을 절대 수정하지 마세요. 대신, 이 기획안의 실행(Execution) 단계를 한 차원 예술적으로 끌어올릴 수 있는 **구체적인 예술적 예시(Reference) 3가지**를 제안하세요.

[예시 작성 절대 원칙]
1. 장르에 경계가 없습니다. 시(Poetry), 디젤의 'Be Stupid' 같은 패션 캠페인, 젠틀몬스터의 설치미술, 현대무용 등 어떤 것이든 가능합니다.
2. 단, 제안한 예시의 이유는 **반드시 앞서 도출된 '크리에이티브 가설' 및 '마케팅 방향'의 뾰족함과 본질적으로 완벽하게 연결**되어야 합니다. (이것이 가장 중요)
3. 3가지 예시를 작성할 때, 각 예시의 특성에 맞게 서술을 강화하세요:
   - 시각적인 예시라면 '시각적 이미지'를 극대화하여 묘사
   - 과정이 중요한 예시라면 '과정을 설명하는 논리'를 강조
   - 컨셉추얼한 예시라면 '컨셉 그 자체'를 강조
**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**"""),
            ("user", "브리프: {brief}\n\n도출된 아이디어:\n{agile_ideas}\n\n마케팅 전략:\n{perf_data}")
        ])
        return (prompt | llm).invoke({"brief": brief, "agile_ideas": agile_ideas, "perf_data": perf_data}).content

    artistic_references = run_art_director()

    return {
        "research_data": research_data,
        "micro_tribe_analysis": micro_tribe,
        "cultural_tensions": micro_tribe, # merging concept for backward compatibility
        "agile_ideas": agile_ideas,
        "performance_data": perf_data,
        "artistic_references": artistic_references
    }

def synthesize_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] SYNTHESIZE (Muad'Dib Prescience + Zero-Loss Aggregation) ---")
    res = state.get("research_data", "")
    ana = state.get("micro_tribe_analysis", "")
    ide = state.get("agile_ideas", "")
    mar = state.get("performance_data", "")
    art = state.get("artistic_references", "")
    
    llm = get_openai_llm()
    
    # 최고 전략 책임자(CSO) 통찰 추출
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 과거의 인사이트와 현재의 SNS 흐름을 동시에 꿰뚫어 보는 최고 전략 책임자(CSO)입니다. 
아래 수집된 리서치(현재 SNS 흐름)와 텐션 분석, 그리고 기초 아이디어들을 바탕으로, **"지금 이 시대가 본질적으로 요구하는 거시적 결핍(Deficiency)과 이를 해결할 단 하나의 날카로운 시대적 전략 명제"**를 3~4문단으로 묵직하게 도출하세요.
이 통찰은 기획서 전체를 관통하는 영혼(Soul)이 됩니다."""),
        ("user", "리서치 및 SNS 흐름:\n{res}\n\n타겟/텐션 분석:\n{ana}\n\n도출된 아이디어 가설:\n{ide}")
    ])
    
    prescience_response = (prompt | llm).invoke({"res": res, "ana": ana, "ide": ide})
    prescience_insight = prescience_response.content
    
    # LLM 요약을 최소화하고 문자열을 100% 그대로 이어붙입니다 (Append)
    blueprint = f"""# 0. 시대적 통찰 및 전략 명제 (Muad'Dib's Prescience)
{prescience_insight}

# 1. 리서치 데이터 (Research)
{res}

# 2. 타겟 및 텐션 분석 (Analysis)
{ana}

# 3. 애자일 크리에이티브 가설 (Ideas)
{ide}

# 4. 퍼포먼스 마케팅 및 매체 전략 (Marketing)
{mar}

# 5. 예술적 레퍼런스 및 승화 전략 (Artistic Layer)
{art}"""
    
    return {"blueprint": blueprint}

def get_psychology_principles():
    import os
    notes_path = os.path.join(os.path.dirname(__file__), "psychology_principles.md")
    try:
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                return f"\n[설득의 심리학 및 행동경제학 지식 베이스]:\n{f.read().strip()}\n"
    except Exception as e:
        print(f"[SYSTEM] 심리학 지식 베이스 로드 오류: {e}")
    return ""

def hook_strategy_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] HOOK STRATEGY & PSYCHOLOGY AUTO-ROUTING ---")
    llm = get_openai_llm()
    psychology_notes = get_psychology_principles()
    
    strategies = """1. [이성] 실행 지연 비용 (Cost of Inaction): "지금 방치하면 1년 뒤 OOO억 원을 잃게 됩니다."
2. [이성] 벤치마크 위협 (Benchmark Threat): 경쟁사/시장 평균 데이터와 극명한 갭을 보여주어 조용한 위기감 조성.
3. [감성] 역설적 데이터 쇼크 (Paradox Data Shock): 업계 상식을 박살 내는 단 하나의 충격적 반전 데이터.
4. [감성] 도발적 질문 (Provocative Question): "당신의 예산 80%가 허공에 버려지고 있다면?"
5. [감성] 초미시 페르소나 (Micro-Persona Empathy): 특정 1명의 서늘한 검색 기록이나 일상을 현미경처럼 클로즈업."""

    tone_and_manner = state.get("tone_and_manner", "🤖 AI 자동 판단")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 최고 수준의 프레젠테이션 디렉터이자 인간 심리 분석가입니다. 
캠페인 브리프와 수집된 블루프린트 데이터를 분석하여, 제안서 도입부(Hook)에 쓸 가장 강력한 '후킹 전략' 1가지를 다음 5개 중에서 선택하세요.

[5가지 훅 전략 옵션]
{{strategies}}

선택 기준: 
- B2B, 퍼포먼스 마케팅, 점유율 방어 목적이면 이성적 전략(1, 2)이 유리합니다.
- 새로운 트렌드, 리포지셔닝, 인식 전환이 목적이면 감성적 전략(3, 4, 5)이 유리합니다.
- 사용자가 지정한 톤앤매너 요구사항이 있다면 최우선으로 존중하세요. (요구사항: {{tone_and_manner}})

[심리학 기반 설계 필수]
선택한 훅 전략이 인간의 어떤 본성을 자극하는지 아래 [지식 베이스]를 참조하여 명확히 뼈대를 세우세요.
{{psychology_notes}}

[출력 형식] - 반드시 아래 형식을 정확히 지켜주세요.
선택된 전략: [1~5 중 하나를 그대로 적으세요. 예: 4. [감성] 도발적 질문 (Provocative Question)]
선택 이유: [선택한 훅 전략이 현재 맥락에 왜 가장 강력한지 논리적으로 설명하되, 반드시 "이 전략은 인간의 [손실 회피 편향]과 [희귀성의 법칙]을 자극하기 위함입니다"와 같이 구체적인 심리학적 트리거를 포함하여 3문장 이내로 작성하세요.]"""),
        ("user", "캠페인 브리프:\n{brief}\n\n데이터 블루프린트:\n{blueprint}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        strategies=strategies,
        tone_and_manner=tone_and_manner,
        psychology_notes=psychology_notes,
        brief=state.get("brief", ""),
        blueprint=state.get("blueprint", "")
    ))
    
    content = response.content
    selected = "3. [감성] 역설적 데이터 쇼크 (Paradox Data Shock)"
    reasoning = "분석에 기반하여 기본 훅 전략과 심리적 트리거가 설정되었습니다."
    
    import re
    match_strategy = re.search(r"선택된 전략:\s*(.*)", content)
    match_reason = re.search(r"선택 이유:\s*(.*)", content, re.DOTALL)
    
    if match_strategy:
        selected = match_strategy.group(1).strip()
    if match_reason:
        reasoning = match_reason.group(1).strip()
        
    return {"selected_hook_strategy": selected, "hook_reasoning": reasoning}

def parallel_report_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] PARALLEL REPORT GENERATION (Sec1, Sec2, Sec3, Appendix) ---")
    
    def run_sec1():
        return report_sec1_node(state)["report_sec1"]

    def run_sec2():
        return report_sec2_node(state)["report_sec2"]

    def run_sec3():
        return report_sec3_node(state)["report_sec3"]

    def run_appendix():
        return report_appendix_node(state)["report_appendix"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f1 = executor.submit(run_sec1)
        f2 = executor.submit(run_sec2)
        f3 = executor.submit(run_sec3)
        f_appx = executor.submit(run_appendix)
        
        sec1 = f1.result()
        sec2 = f2.result()
        sec3 = f3.result()
        appx = f_appx.result()

    return {
        "report_sec1": sec1,
        "report_sec2": sec2,
        "report_sec3": sec3,
        "report_appendix": appx
    }
