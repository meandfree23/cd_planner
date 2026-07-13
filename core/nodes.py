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
    return ChatOpenAI(model="gpt-4o", temperature=0.3)

def web_search_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] WEB SEARCH (DUCKDUCKGO) ---")
    brief = state["brief"]
    llm = get_openai_llm()
    
    # 1. Extract 3 keywords
    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 리서치 전문가입니다. 다음 브리프를 보고 가장 최신의 팩트, 뉴스, 트렌드를 찾기 위한 구글 검색 쿼리 3개를 작성해주세요. 리스트 형태의 JSON으로 반환해야 합니다. 예시: [\"쿼리1\", \"쿼리2\", \"쿼리3\"]"),
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
                results = ddgs.text(q, max_results=3)
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
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 20페이지 분량의 [심층 결과 분석 보고서]를 작성하는 최고 수준의 비즈니스 및 전략 컨설턴트입니다.

[절대 금지 사항 - 위반 시 실패]
1. "이 프레젠테이션은 기획팀, 마케팅팀, CD가 조율한 결과입니다" 또는 "우리는 A/B 테스트를 통해 검증했습니다"와 같은 [기획의 과정이나 방법론(메타 발언)]을 절대 언급하지 마세요. 방법론은 백그라운드에 감추고 오직 도출된 [구체적인 결과와 날카로운 분석]만 이야기하세요.
2. 겉핥기식의 요약된 문장을 쓰지 마세요.
3. [분석의 절대 원칙]: 절대 '추가 정보가 필요하다'며 작성을 포기하거나 거절하지 마세요. 데이터가 부족하더라도 수집된 최소한의 팩트들을 엮어, 명확한 인과관계(Reason Why)가 증명된 논리적 추론으로 내용을 당당하게 100% 완성하세요.

지금은 **[Part 1: 현상 분석 및 원인 규명 - HOOK & ATTENTION] (슬라이드 1~7)** 파트입니다.

작성 규칙:
1. 슬라이드 구분을 명확히 하되, 반드시 다음 7개의 슬라이드를 누락 없이 각각 모두 상세히 작성하세요. (단 하나의 슬라이드도 생략 금지)
   - ## Slide 1: [브랜드/주제 소개 및 탄생 배경]
   - ## Slide 2: [기존 시장/경쟁 환경의 한계와 고질적 문제점]
   - ## Slide 3: [브랜드/제품만의 독보적 기술 또는 전략적 특장점]
   - ## Slide 4: [주요 성과, 파트너십 또는 초기 반응 지표]
   - ## Slide 5: [실질적인 소비자 혜택 및 효용 가치 지표]
   - ## Slide 6: [과거부터 현재까지의 시장 가치 변화 또는 트렌드 추이]
   - ## Slide 7: [최근 거시적 시장 동향과 브랜드의 현재 위치]
2. 각 슬라이드의 [PT 스크립트]는 대단히 길고, 풍부하고, 구체적인 논술형이어야 합니다. (슬라이드당 최소 300자 이상)
3. 수집된 데이터(리서치, 통계 수치)를 적극 활용하여, 대상 현상 이면에 숨겨진 '결정적 원인'을 심층적으로 파고드세요.
4. 최소 2개 이상의 슬라이드에는 현상을 직관적으로 증명하는 `mermaid` 차트 코드를 삽입하세요.

{heidi_notes}
{feedback_context}"""),
        ("user", "브리프: {brief}\n\n분석 기반 데이터:\n{research_data}\n{performance_data}")
    ])
    
    feedback_context = f"\n[🎨 이전 PPT 디자이너(Report 에이전트)의 역방향 피드백 반영 사항]\n디자이너의 요청: {state['designer_feedback']}\n이번 기획서 작성 시, 위 디자이너의 피드백을 최우선으로 반영하여 글의 호흡이나 데이터 구조, 포맷을 유동적으로 진화시키세요.\n" if state.get("designer_feedback") else ""
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        feedback_context=feedback_context,
        brief=state["brief"],
        research_data=state.get("research_data", ""),
        performance_data=state.get("performance_data", "")
    ))
    return {"report_sec1": response.content}


def report_sec2_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT SEC 2: 타겟 분석 및 전략 ---")
    llm = get_openai_llm()
    heidi_notes = get_heidi_design_notes()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 20페이지 분량의 [심층 결과 분석 보고서]를 작성하는 최고 수준의 타겟 전략 분석가입니다.

[절대 금지 사항 - 위반 시 실패]
1. "기획의 과정, 방법론, 분석 툴"에 대한 이야기는 일절 배제하세요. 오로지 도출된 분석의 [실질적 결과와 핵심 방향]에만 집중하세요.
2. 겉핥기식의 뻔한 설명을 배제하고, 독창적이고 심도 깊은 통찰력을 보여주세요.
3. [분석의 절대 원칙]: 절대 '추가 정보가 필요하다'며 작성을 포기하거나 거절하지 마세요. 데이터가 부족하더라도 수집된 최소한의 팩트들을 엮어, 명확한 인과관계(Reason Why)가 증명된 논리적 추론으로 내용을 당당하게 100% 완성하세요.

지금은 **[Part 2: 타겟 집단의 심리 및 구조적 갈등 - DEEP PERSUASION] (슬라이드 8~14)** 파트입니다.

작성 규칙:
1. 슬라이드 구분을 명확히 하되, 반드시 다음 7개의 슬라이드를 누락 없이 각각 모두 상세히 작성하세요. (단 하나의 슬라이드도 생략 금지)
   - ## Slide 8: [주요 타겟 집단(마이크로 트라이브) 프로파일링 분석]
   - ## Slide 9: [타겟 집단이 겪고 있는 본질적인 미충족 요구(Unmet Needs)]
   - ## Slide 10: [시장과 타겟 사이에 존재하는 사회적/문화적 텐션(Tension) 해부]
   - ## Slide 11: [새로운 솔루션/제품 도입이 타겟 생태계에 미칠 즉각적 영향]
   - ## Slide 12: [브랜드가 제안하는 핵심 가치와 규제/시장 표준 준수 강점]
   - ## Slide 13: [거시적 환경 변화(정책, 트렌드 등)에 따른 기회 요인 분석]
   - ## Slide 14: [전통적 방식과 새로운 솔루션의 상호 보완성 및 시너지]
2. 각 슬라이드의 [PT 스크립트]는 풍부한 사례와 근거를 들어 아주 상세하게 논술해야 합니다. (슬라이드당 최소 300자 이상)
3. 대상 타겟층(마이크로 트라이브)의 기저에 깔린 사회적/문화적 텐션(Tension)이나 미충족 요구(Unmet Needs)를 깊이 해부하고, 이것이 왜 발생하는지 비즈니스적/구조적 인과 관계를 증명하세요.
4. 타겟의 행동 여정이나 상호작용의 흐름을 시각화하는 `mermaid` 흐름도(graph TD) 코드를 최소 2개 삽입하세요.

{heidi_notes}"""),
        ("user", "브리프: {brief}\n\n트라이브 및 텐션 데이터:\n{micro_tribe_analysis}\n{cultural_tensions}\n\n추가 데이터:\n{performance_data}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
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
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 20페이지 분량의 [심층 결과 분석 보고서]를 작성하는 최고 수준의 미래 전략 및 기대 효과 분석가입니다.

[절대 금지 사항 - 위반 시 실패]
1. "A/B 테스트를 하겠다, 캠페인을 실행하겠다, KPI 목표는 이러하다" 와 같은 임시적 마케팅 대행 실행론(방법론)에 그치지 마세요.
2. 당신은 단순 실행을 단편 기획하는 것이 아니라, 현 분석 결과를 디딤돌 삼아 "도래할 장기적인 가치, 미래 상용화 전망, 비즈니스적 시너지 및 사회경제적 파급 효과"를 거시적이고 전문적으로 전망하는 사람입니다.
3. [분석의 절대 원칙]: 절대 '추가 정보가 필요하다'며 작성을 포기하거나 거절하지 마세요. 데이터가 부족하더라도 수집된 최소한의 팩트들을 엮어, 명확한 인과관계(Reason Why)가 증명된 논리적 추론으로 내용을 당당하게 100% 완성하세요.

지금은 **[Part 3: 미래 비전 예측 및 창조적 결론 - CLIMAX & IMPACT] (슬라이드 15~20)** 파트입니다.

작성 규칙:
1. 슬라이드 구분을 명확히 하되, 반드시 다음 6개의 슬라이드를 누락 없이 각각 모두 상세히 작성하세요. (단 하나의 슬라이드도 생략 금지)
   - ## Slide 15: [단기적(1~2년 내) 브랜드 로드맵 및 시장 활성화 기대 효과]
   - ## Slide 16: [중기적(3~5년 내) 비즈니스 성장 및 점유율 예측 분석]
   - ## Slide 17: [장기적(5년 이상) 거시적 파급 효과 및 미래 가치 전망]
   - ## Slide 18: [브랜드 성장에 따른 비즈니스 선순환(플라이휠) 메커니즘 분석]
   - ## Slide 19: [경쟁 브랜드와의 결정적 차별성 및 미래 리스크 극복 전략]
   - ## Slide 20: [결론: 글로벌/사회적 가치 창출(ESG) 및 생태계 상생 비전]
2. 각 슬라이드의 [PT 스크립트]는 통계적 수치와 논리적 추론을 바탕으로 한, 가장 밀도 높고 통찰력 있는 장문의 논술(최소 300자 이상)이어야 합니다.
3. 분석된 결과를 바탕으로, 앞으로 시장, 산업, 또는 사회에 도래할 구체적인 변화와 그로 인한 수치적 파급 효과(결과적 지표)를 창조적으로 예측하여 쐐기를 박으세요.
4. 미래의 발전 마일스톤이나 구체적인 로드맵/타임라인을 보여주는 `mermaid` 차트를 최소 2개 삽입하세요.

{heidi_notes}"""),
        ("user", "브리프: {brief}\n\n기초 아이디어 가설:\n{agile_ideas}\n\n추가 지표 데이터:\n{performance_data}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        heidi_notes=heidi_notes,
        brief=state["brief"],
        agile_ideas=state.get("agile_ideas", ""),
        performance_data=state.get("performance_data", "")
    ))
    return {"report_sec3": response.content}


def report_merge_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] REPORT MERGE ---")
    
    sec1 = state.get("report_sec1", "")
    sec2 = state.get("report_sec2", "")
    sec3 = state.get("report_sec3", "")
    
    final_markdown = f"""# 📈 [심층 프레젠테이션] CD 플래닝 마스터 보고서

> 본 보고서는 통계 데이터와 시각화 차트를 포함한 20장 분량의 프리젠테이션 대본 양식으로 작성되었습니다.

{sec1}

---

{sec2}

---

{sec3}
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
제출된 20페이지 분량의 기획서를 꼼꼼히 평가하세요.

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
4. **반드시 Slide 1부터 Slide 20까지 총 20개의 슬라이드 전체를 단 하나도 생략하거나 축약하지 말고 차례대로 100% 전부 매핑하여 출력하세요.** 모델의 출력 토큰 한계에 도달하지 않도록 텍스트를 구조화하되, 슬라이드의 개수는 반드시 정확하게 20개여야 합니다.

{heidi_notes}
{feedback_context}

반드시 마크다운 코드블록(```text ... ```) 안에 담아주세요.

출력 포맷 예시 (이 구조를 반복하여 20장의 슬라이드를 완벽하게 구성하세요):
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
    print("--- [NODE] PRESENTATION EVALUATOR & JUDGE ---")
    llm = get_openai_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 광고 대행사의 프레젠테이션(PT)을 엄격하게 심사하는 15년 차 시니어 심사위원(Judge) 에이전트입니다.
제출된 광고 기획서(Report)와 PPT 파싱 코드를 면밀히 검수하고, 다음 기준에 따라 날카로운 피드백과 지적 사항을 담은 [프리젠테이션 심사 보고서]를 작성해주세요.

심사 기준:
1. **논리적 타당성**: 서론(문제 제기) - 본론(트라이브 분석 및 솔루션) - 결론(퍼포먼스 마케팅 및 미래 지표)으로 이어지는 흐름에 논리적 모순이나 약점이 없는가?
2. **크리에이티브의 참신성**: 크리에이티브 메시지나 애자일 가설이 뻔하지 않고 타겟의 심리를 날카롭게 찌르고 있는가?
3. **데이터 기반의 구체성**: 통계치(예: 투표율 61%, CTR 등)나 벤치마크 숫자들이 구체적으로 제시되었으며, 타당한 근거가 있는가?
4. **시각화 레이아웃 적합성**: mermaid 차트(파이 차트, 간트 차트 등)의 구성과 배치가 슬라이드의 흐름과 어울리는가?

심사 보고서 마크다운 템플릿:
# 👩‍⚖️ 프리젠테이션 심사위원 검수 보고서

## 1. 📊 종합 평가 및 심사 평점
- **종합 점수**: [점수] / 10
- **한 줄 심사평**: [기획서를 관통하는 날카로운 한 줄 요약평]

## 2. 🌟 주요 강점 (Points of Praise)
- [기획서에서 특히 뛰어난 점 2~3가지를 명확한 근거와 함께 칭찬]

## 3. ⚠️ 치명적 약점 및 문제점 발견 (Problems Found)
- [논리적 비약이나 약점, 보완이 필요한 부분 2~3가지를 날카롭게 지적]

## 4. 🛠️ 즉시 반영 가능한 수정 요청 사항 (Revise Requests)
- [사용자나 다른 에이전트가 바로 수정/보완할 수 있는 구체적인 지시 사항 및 대안 제안]

존댓말로 격식 있고 날카로운 카리스마를 담아 작성해주세요."""),
        ("user", "캠페인 브리프: {brief}\n\n최종 기획서 원문:\n{final_report}\n\nPPT 파싱 코드:\n{ppt_code}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        brief=state["brief"],
        final_report=state.get("final_report", ""),
        ppt_code=state.get("ppt_code", "")
    ))
    return {"evaluation_report": response.content}


# =====================================================================
# PHASE 4: PARALLEL MULTI-AGENT ARCHITECTURE
# =====================================================================

def parallel_ideation_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] HYBRID IDEATION (Research/Analysis -> Idea/Marketing) ---")
    brief = state["brief"]
    web_context = state.get("web_context", "")
    llm = get_openai_llm()
    
    def run_research():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 최고 수준의 리서처입니다. 주어진 브리프와 웹 검색 컨텍스트를 바탕으로 타겟 소비자의 라이프스타일, 트렌드, 그리고 마이크로 트라이브(Micro-Tribe)를 3가지로 압축해 분석하세요.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context}).content

    def run_analysis():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 예리한 전략 분석가입니다. 주어진 브리프와 웹 컨텍스트를 보고 타겟 소비자들이 겪고 있는 핵심 갈등과 컬처럴 텐션(Cultural Tension)을 3가지 도출하세요. 인과관계가 명확해야 합니다.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context}).content

    # 1. First Phase: Research & Analysis (Parallel)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_res = executor.submit(run_research)
        f_ana = executor.submit(run_analysis)
        research_data = f_res.result()
        micro_tribe = f_ana.result()

    # 2. Second Phase: Ideation & Marketing (Parallel, strictly based on Phase 1 results)
    def run_idea():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 파격적인 크리에이티브 디렉터입니다. 브리프와 수집된 트렌드, 그리고 **앞서 분석된 타겟 텐션(Tension)**을 바탕으로 소비자를 유혹할 애자일 크리에이티브 가설(Agile Idea) 3가지를 도출하세요. **특히 컨텍스트 내에 '최신 디자인/마케팅 트렌드'가 있다면 아이디어에 강제로 결합시켜 매우 동시대적인 제안을 만드세요.** 반드시 앞선 전략가의 '텐션 분석'을 본질적으로 해결하는 아이디어여야 합니다.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}\n\n전략가의 타겟/텐션 분석:\n{analysis_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context, "analysis_context": micro_tribe}).content
        
    def run_marketing():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 퍼포먼스 마케터입니다. 브리프와 전략가의 '타겟/텐션 분석' 결과를 바탕으로, 이 타겟에게 도달하기 위한 핵심 매체 믹스, 예상 KPI(CPC/CTR), A/B 테스트 전략을 수립하세요.\n**[중요] 반드시 모든 문장과 단어를 한국어(Korean)로 상세하게 작성하세요.**"),
            ("user", "브리프: {brief}\n웹 검색: {web_context}\n\n전략가의 타겟/텐션 분석:\n{analysis_context}")
        ])
        return (prompt | llm).invoke({"brief": brief, "web_context": web_context, "analysis_context": micro_tribe}).content

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_ide = executor.submit(run_idea)
        f_mar = executor.submit(run_marketing)
        agile_ideas = f_ide.result()
        perf_data = f_mar.result()

    return {
        "research_data": research_data,
        "micro_tribe_analysis": micro_tribe,
        "cultural_tensions": micro_tribe, # merging concept for backward compatibility
        "agile_ideas": agile_ideas,
        "performance_data": perf_data
    }

def synthesize_node(state: PlannerState) -> PlannerState:
    print("--- [NODE] SYNTHESIZE (Zero-Loss Aggregation) ---")
    res = state.get("research_data", "")
    ana = state.get("micro_tribe_analysis", "")
    ide = state.get("agile_ideas", "")
    mar = state.get("performance_data", "")
    
    # LLM 요약을 완전히 배제하고 문자열을 100% 그대로 이어붙입니다 (Append)
    blueprint = f"""# 1. 리서치 데이터 (Research)
{res}

# 2. 타겟 및 텐션 분석 (Analysis)
{ana}

# 3. 애자일 크리에이티브 가설 (Ideas)
{ide}

# 4. 퍼포먼스 마케팅 및 매체 전략 (Marketing)
{mar}"""
    
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
    print("--- [NODE] PARALLEL REPORT GENERATION (Sec1, Sec2, Sec3) ---")
    blueprint = state.get("blueprint", "")
    hook_strategy = state.get("selected_hook_strategy", "기본 훅 전략")
    hook_reasoning = state.get("hook_reasoning", "")
    llm = get_openai_llm()
    
    def run_sec1():
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"당신은 기획서 도입부를 매혹적으로 짜는 전문가입니다. 전체 블루프린트 중에서 '1. 리서치 데이터'와 '2. 타겟 및 텐션 분석'을 바탕으로 **'{{hook_strategy}}'** 전략을 철저히 반영하여 도입부(Hook) 텍스트를 마크다운으로 재구성하세요.\n\n[심리학적 설계 지침]\n이 전략의 선택 이유는 다음과 같습니다: **{{hook_reasoning}}**\n이 심리적 트리거(예: 손실 회피, 희귀성 등)가 청중의 무의식을 강타하도록 텍스트의 논리와 카피를 가장 날카롭고 강렬하게 각색하세요. 블루프린트의 팩트를 활용하되 긴장감을 극대화하세요."),
            ("user", "블루프린트: {blueprint}")
        ])
        return (prompt | llm).invoke({"hook_strategy": hook_strategy, "hook_reasoning": hook_reasoning, "blueprint": blueprint}).content

    def run_sec2():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 기획서 작성 전문가입니다. 전체 블루프린트 중에서 **'3. 애자일 크리에이티브 가설 (Ideas)'에 해당하는 내용만을 정확히 추출**하세요. 단, 추출한 해당 파트의 텍스트는 **단 한 글자도 요약하거나 생략하지 말고 100% 보존**하여 마크다운 포맷으로 정리해야 합니다. 리서치나 마케팅 파트의 내용은 절대 가져오지 마세요."),
            ("user", "블루프린트: {blueprint}")
        ])
        return (prompt | llm).invoke({"blueprint": blueprint}).content

    def run_sec3():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 기획서 작성 전문가입니다. 전체 블루프린트 중에서 **'4. 퍼포먼스 마케팅 및 매체 전략 (Marketing)'에 해당하는 내용만을 정확히 추출**하세요. 단, 추출한 해당 파트의 텍스트는 **단 한 글자도 요약하거나 생략하지 말고 100% 보존**하여 마크다운 포맷으로 정리해야 합니다. 리서치나 아이디어 파트의 내용은 절대 가져오지 마세요."),
            ("user", "블루프린트: {blueprint}")
        ])
        return (prompt | llm).invoke({"blueprint": blueprint}).content

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f1 = executor.submit(run_sec1)
        f2 = executor.submit(run_sec2)
        f3 = executor.submit(run_sec3)
        
        sec1 = f1.result()
        sec2 = f2.result()
        sec3 = f3.result()

    return {
        "report_sec1": sec1,
        "report_sec2": sec2,
        "report_sec3": sec3
    }
