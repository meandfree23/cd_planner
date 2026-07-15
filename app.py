import streamlit as st
import os
import time
import json
from dotenv import load_dotenv

from core.graph import build_planner_graph
from core.state import PlannerState

# DB 파일 경로
FEEDBACK_DB_PATH = "data/feedback_db.json"

def load_feedback_db():
    if not os.path.exists(FEEDBACK_DB_PATH):
        return []
    try:
        with open(FEEDBACK_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_feedback(feedback_text):
    if not feedback_text.strip(): return
    os.makedirs(os.path.dirname(FEEDBACK_DB_PATH), exist_ok=True)
    db = load_feedback_db()
    db.append({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "content": feedback_text.strip()})
    with open(FEEDBACK_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_merged_feedback():
    db = load_feedback_db()
    if not db: return ""
    return "\n\n".join([f"[{item['timestamp']}] {item['content']}" for item in db])

# .env 환경 변수 로드
load_dotenv()

def extract_headline(report_content, brief_input=""):
    import re
    # 1. Slide 1의 대괄호 안의 제목 찾기: Slide 1: [새로운 휴식의 시작...]
    match = re.search(r"Slide 1:\s*\[(.*?)\]", report_content)
    if match:
        return match.group(1).strip()
    
    # 2. Slide 1의 큰따옴표 안의 제목 찾기: Slide 1: [파격적인 후킹 타이틀]\n"2026 지방선거: 새로운 정치 지형의 시작!"
    match_quote = re.search(r"Slide 1:[^\n]*\n\s*\"([^\"]+)\"", report_content)
    if match_quote:
        return match_quote.group(1).strip()

    # 3. Slide 1 아래 첫 따옴표 안의 문장 찾기
    match_quote_sec = re.search(r"Slide 1:.*?\n.*?\"([^\"]+)\"", report_content, re.DOTALL)
    if match_quote_sec:
        return match_quote_sec.group(1).strip()
        
    # 4. 첫 번째 마크다운 샵(#) 제목 찾기 (Campaign Brief 는 제외)
    lines = report_content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith("# ") and "Campaign Brief" not in line:
            return line[2:].strip()
            
    # 5. Slide 1: 제목 형식 찾기
    match2 = re.search(r"Slide 1:\s*(.*)", report_content)
    if match2:
        return match2.group(1).strip()
        
    # 6. 정 안되면 브리프 첫 줄 또는 기본값
    if brief_input:
        first_line = brief_input.strip().split('\n')[0]
        if len(first_line) > 20:
            return first_line[:20] + "..."
        return first_line
    return "무제 기획서"

def safe_filename(name):
    import re
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = cleaned.strip().replace(" ", "_")
    if not cleaned:
        cleaned = "report"
    return cleaned

def generate_html_report(ppt_content, title):
    from core.nodes import get_openai_llm
    from langchain_core.prompts import ChatPromptTemplate
    llm = get_openai_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 최고 수준의 프론트엔드/웹 디자이너입니다. 전달받은 기획서 텍스트 원본을 훼손하지 말고, 최신 AI 하이엔드 디자인 방법론(글래스모피즘, 1920x1080 단일 뷰포트 고정, 극단적 타이포그래피 스케일, 마이크로 애니메이션)을 적용해 완벽한 단일 HTML 문서를 렌더링하세요. 마크다운 블록(```html)을 제외하고 순수 HTML만 리턴하세요."),
        ("user", f"제목: {title}\n\n기획서 내용:\n{ppt_content}")
    ])
    try:
        response = llm.invoke(prompt.format_messages())
        content = response.content
        if content.startswith("```html"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
    except Exception as e:
        return f"<html><body><h1>Error rendering HTML</h1><p>{e}</p></body></html>"

from core.pptx_renderer import create_pptx_file

def send_to_report_agent(ppt_content, filename):
    import pyperclip
    # 1. Write to auto-ot input_raw.txt (상대 경로로 변경하여 Cloud 호환성 확보)
    target_path = "data/input_raw.txt"
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as tf:
            tf.write(ppt_content)
    except Exception as e:
        return False, f"local file write failed: {e}"
        
    # 2. 클립보드 복사 (report 에이전트와의 명확한 역할 분담 가이드 포함)
    try:
        message_text = f"""[PLANNER 에이전트 업무 이관]
새로운 마스터 기획서 코드({filename})가 도착했습니다.

🤝 **[Plan ↔ Report 에이전트 협업 가이드]**
1. **내용 100% 유지 (No Summary):** 본 코드는 기획 팀과 QA 심사위원의 검증을 마친 '최종 스크립트'입니다. 임의로 요약, 압축, 왜곡하지 말고 텍스트를 그대로 보존해 주세요.
2. **역할 분담 (Design Focus):** 기획/분석/논리는 plan 에이전트가 책임집니다. report 에이전트님은 이 방대한 텍스트가 타겟에게 가장 잘 먹히도록 '시각적 레이아웃, 도식화, 차트 구성' 등 디자인 및 PPT 렌더링에만 모든 리소스를 집중해 주세요.

---
[PPT 파싱 코드 원본]
{ppt_content}"""
        pyperclip.copy(message_text)
        return True, "클립보드에 복사되었습니다. 'report😁' 대화창에 붙여넣기(Ctrl+V/Cmd+V) 해주세요!"
    except Exception as e:
        return False, f"클립보드 복사 실패: {e}"

st.set_page_config(page_title="AI Creative Director", page_icon="✨", layout="wide")

st.title("✨ AI Creative Director Planner")
st.markdown("광고 캠페인 브리프를 입력하면 딥리서치부터 인사이트 발굴, 크리에이티브 아이디어 발상, 최종 기획서 작성까지 자동으로 수행합니다.")

@st.dialog("🎨 렌더링된 단일 HTML 웹 프레젠테이션", width="large")
def show_html_preview(html_content):
    st.components.v1.html(html_content, height=800, scrolling=True)

# 메인 UI
tab1, tab2, tab3 = st.tabs(["🚀 기획안 생성기", "📁 기획서 보관함 (스크랩)", "📰 일일 트렌드 & 아트 인사이트"])

with tab1:
    st.markdown("### 🎯 캠페인 브리프 세팅 (Structured Form)")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        project_name = st.text_input("📦 프로젝트 / 브랜드명", placeholder="예: 무설탕 에너지 음료 '스파크'")
        target_audience = st.text_input("👥 핵심 타겟", placeholder="예: 야근이 잦고 피로감을 느끼는 20대 직장인")
    with col_b2:
        goal = st.selectbox("🎯 핵심 목표 (Goal)", ["매출 하락 방어", "경영진 설득 및 예산 확보", "경쟁사 점유율 탈환", "신규 타겟 유입 및 인지도 제고", "리브랜딩 및 포지셔닝 전환"])
        tone_and_manner = st.selectbox("✨ 원하는 훅(Hook) 전략 및 톤앤매너", [
            "🤖 AI 자동 판단 (최적의 전략을 스스로 탐색)",
            "📊 [이성] 실행 지연 비용 (Cost of Inaction)",
            "📊 [이성] 벤치마크 위협 (Benchmark Threat)",
            "🔥 [감성] 역설적 데이터 쇼크 (Paradox Data Shock)",
            "🔥 [감성] 도발적 질문 (Provocative Question)",
            "📖 [감성] 초미시 페르소나 (Micro-Persona Empathy)"
        ])
    
    additional_context = st.text_area("📝 추가 기획 배경 및 요구사항", height=100, placeholder="예: 경쟁사 '레드불'의 점유율을 뺏어오고 싶습니다.")
    brand_url = st.text_input("🔗 브랜드/기업 공식 웹사이트 URL (선택)", placeholder="예: https://kimsungmin.co.kr/")
    
    # 파이프라인 하위 호환성을 위해 하나로 병합된 brief 텍스트 생성
    brief_input = f"[프로젝트/브랜드명]: {project_name}\n[핵심 타겟]: {target_audience}\n[목표]: {goal}\n[톤앤매너/훅 전략]: {tone_and_manner}\n[추가 배경]: {additional_context}"
    
    with st.expander("🧠 디자이너 피드백 지식창고 (RAG)", expanded=False):
        st.markdown("`report😁` 에이전트가 알려준 과거의 뼈아픈 역방향 피드백들을 이곳에 영구 저장해두세요. 파이프라인이 돌 때 이 지식창고를 전부 읽고 자동으로 기획에 반영합니다.")
        
        # 새로운 피드백 추가
        col_fb1, col_fb2 = st.columns([4, 1])
        with col_fb1:
            new_feedback = st.text_input("새로운 피드백 추가", placeholder="예: [SLIDE 5]의 핵심 팩트는 2줄 이내로 맞춰주세요.")
        with col_fb2:
            st.write("") # 줄맞춤
            st.write("")
            if st.button("💾 DB 저장"):
                if new_feedback:
                    save_feedback(new_feedback)
                    st.success("지식창고에 저장되었습니다!")
                else:
                    st.warning("내용을 입력하세요.")
        
        # 저장된 피드백 리스트업
        st.markdown("#### 📚 누적된 피드백 목록")
        db = load_feedback_db()
        if db:
            for item in reversed(db):
                st.info(f"**{item['timestamp']}**\n\n{item['content']}")
        else:
            st.write("아직 저장된 피드백이 없습니다.")
    
    if st.button("🚀 CD 플래닝 시작", type="primary"):
        try:
            env_openai = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            if env_openai: os.environ["OPENAI_API_KEY"] = env_openai
        except:
            env_openai = os.getenv("OPENAI_API_KEY", "")
        
        if not brief_input.strip():
            st.warning("브리프를 입력해주세요.")
        elif not env_openai or env_openai == "your_openai_api_key_here":
            st.error("OpenAI API Key가 설정되지 않았습니다. 터미널에서 `python setup_keys.py`를 실행해 키를 입력해주세요.")
        else:
            st.session_state["planner_app"] = build_planner_graph()
            
            # 상태 표시 UI
            status_text = st.empty()
            
            # 단계별 결과 출력을 위한 컬럼
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("💡 Analysis & Insights")
                brand_asset_expander = st.expander("0. Brand Deep Dive & SNS Perception")
                research_expander = st.expander("1. Deep Research (수집된 쿼리 및 데이터)")
                analysis_expander = st.expander("2. Micro-Tribe Analysis")
                insight_expander = st.expander("3. Cultural Tensions & Insight")
            with col2:
                st.subheader("🎨 Ideas & Report")
                idea_expander = st.expander("4. Agile Ideas & Journey")
                perf_expander = st.expander("4.5. Performance Marketing")
                report_expander = st.expander("5. Final Report", expanded=True)
                qa_expander = st.expander("🧐 심사위원 피드백 (QA)", expanded=True)
                ppt_code_expander = st.expander("6. PPT Parsing Code")
                eval_expander = st.expander("⚖️ 다면 심사 위원회 검수 (Multi-Jury)", expanded=True)
                evolution_expander = st.expander("📈 자가 학습 진화 리포트 (Evolution Proof)", expanded=True)
            try:
                status_text.info("에이전트 파이프라인 시작 중...")
                
                # 파이프라인 스트리밍 실행 (단계별 진행 상황 확인)
                app = st.session_state["planner_app"]
                # 지식창고에서 모든 과거 피드백 병합하여 주입
                merged_designer_feedback = get_merged_feedback()
                
                initial_state = {
                    "project_name": project_name,
                    "target_audience": target_audience,
                    "goal": goal,
                    "tone_and_manner": tone_and_manner,
                    "additional_context": additional_context,
                    "brand_url": brand_url,
                    "brief": brief_input,
                    "designer_feedback": merged_designer_feedback,
                    "revision_count": 0,
                    "evaluation_feedback": ""
                }
                full_state = initial_state.copy()
                
                with st.spinner("🧠 딥러닝 기반 CD 플래닝 엔진 가동 중... (심사 점수에 따라 자동 재작업이 발생할 수 있습니다)"):
                    # recursion_limit을 늘려 루프가 끊기지 않도록 방어
                    for output in app.stream(initial_state, {"recursion_limit": 50}):
                        for key, value in output.items():
                            full_state.update(value)
                            
                            if key == "brand_asset_extractor":
                                status_text.info("기업 본질 및 SNS 반응 추출 완료!")
                                with brand_asset_expander:
                                    st.markdown(value.get("brand_assets", ""))
                                    
                            elif key == "parallel_ideation":
                                rev = value.get("revision_count", 0)
                                if rev > 0:
                                    status_text.warning(f"⚠️ [자가 학습 루프] 심사 점수 미달로 기획을 전면 재작성합니다! (재학습: {rev}/2회)")
                                else:
                                    status_text.info("병렬 리서치, 분석 및 마케팅 전략 도출 완료!")
                                with research_expander:
                                    st.write("**Search Queries:**", value.get("search_queries"))
                                    st.text_area("Raw Data", value.get("research_data", "")[:1000] + "...", height=150)
                                with analysis_expander:
                                    st.write(value.get("micro_tribe_analysis", ""))
                                with idea_expander:
                                    st.write(value.get("agile_ideas", ""))
                                with perf_expander:
                                    st.write(value.get("performance_data", ""))
                            
                            elif key == "hook_strategy":
                                status_text.info("🧠 인간 본성(심리학)에 기반한 최적의 후킹 전략을 설계 중입니다...")
                                with st.expander("🎣 Psychology-based Hook Strategy", expanded=True):
                                    st.success(f"**Selected Hook Strategy:** {value.get('selected_hook_strategy')}")
                                    st.info("💡 **심리학적 설계 의도 및 트리거:**")
                                    st.write(value.get("hook_reasoning"))
                                    
                            elif key == "parallel_report":
                                status_text.info("기획서 블루프린트 추출 완료. 병합을 준비합니다...")
                                
                            elif key == "report_merge":
                                status_text.info("마스터 기획서 병합 완료. 심사위원의 검수가 진행중입니다...")
                                with report_expander:
                                    st.markdown(value.get("final_report", ""))
                                    
                            elif key == "qa_judge":
                                status_text.info("심사위원의 퀄리티 검수 완료. PPT 파싱 코드를 추출합니다...")
                                with qa_expander:
                                    st.markdown(value.get("qa_feedback", ""))
                                    
                            elif key == "ppt_code":
                                status_text.info("PPT 파싱 코드 추출 완료. 심사위원 검수를 시작합니다...")
                                with ppt_code_expander:
                                    st.code(value.get("ppt_code", ""), language="text")
                                    
                            elif key == "evaluation":
                                status_text.info("⚖️ 다면 심사 위원회의 검수가 완료되었습니다. 진화 증명 여부를 판단합니다...")
                                with eval_expander:
                                    st.markdown(value.get("evaluation_report", ""))
                                    
                            elif key == "evolution_proof":
                                status_text.success("✨ 20페이지 기획서, 다면 심사 및 자가 학습 진화 증명이 모두 완료되었습니다! (보관함 자동 저장)")
                                with evolution_expander:
                                    st.markdown(value.get("evolution_proof", ""))
                                
                # 리포트 파일 및 PPT 코드 자동 저장 (버그 픽스: full_state 사용)
                if full_state and "final_report" in full_state and "ppt_code" in full_state:
                    report_content = full_state["final_report"]
                    ppt_content = full_state["ppt_code"]
                    eval_content = f"{full_state.get('qa_feedback', '')}\n\n---\n\n{full_state.get('evaluation_report', '')}"
                    
                    if not os.path.exists("reports"):
                        os.makedirs("reports")
                    
                    # LLM을 이용한 똑똑한 네이밍 (정규식 오류 해결)
                    from core.nodes import get_openai_llm
                    naming_llm = get_openai_llm()
                    try:
                        name_resp = naming_llm.invoke(f"다음 브리프 내용을 바탕으로 파일명으로 쓸 3~4단어짜리 짧고 직관적인 기획서 제목(예: 김성민커피_런칭_기획서)을 한국어로 작성해. 부호 없이 단어만 출력:\n{brief_input[:500]}")
                        headline = name_resp.content.strip().replace(" ", "_")
                    except:
                        headline = extract_headline(report_content, brief_input)
                        
                    safe_name = safe_filename(headline)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
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
                            
                    # --- Report 에이전트 자동 연동(Auto-Sync) 저장 로직 ---
                    os.makedirs("data", exist_ok=True)
                    sync_file_path = "data/latest_ppt_sync.txt"
                    timestamp_file_path = "data/sync_timestamp.txt"
                    
                    with open(sync_file_path, "w", encoding="utf-8") as f:
                        f.write(ppt_content)
                    
                    with open(timestamp_file_path, "w", encoding="utf-8") as f:
                        f.write(str(time.time()))
                        
                    
                    # 상태 업데이트로 버튼 증발 방지 및 새 기획서 강조
                    st.session_state["latest_generated_report"] = safe_name
                    
                    st.success(f"최종 기획서 보관함 저장 및 Report 에이전트로의 자동 전송이 완료되었습니다! 🚀")
                    
                    st.info("💡 **PPTX 파일 자동 생성 및 다운로드**는 상단의 **'기획서 보관함 (스크랩)'** 탭에서 이용하실 수 있습니다. (버튼 클릭 오류 방지를 위해 분리되었습니다)")
                    
            except Exception as e:
                status_text.error(f"파이프라인 실행 중 오류가 발생했습니다: {e}")

with tab2:
    st.subheader("📁 기획서 보관함 (히스토리)")
    st.markdown("컴퓨터를 껐다 켜거나 새로고침을 해도, 이전에 작업한 모든 기획서(.md)와 PPT 코드(.txt)가 영구적으로 보관됩니다.")
    
    # [BUGFIX] 방금 생성한 기획서를 탭 1에서도 즉각 접근할 수 있도록 UI 추가
    if st.session_state.get("latest_generated_report"):
        latest_name = st.session_state["latest_generated_report"]
        st.info(f"✨ 방금 생성된 기획서 **'{latest_name}'** 가 보관함에 업데이트 되었습니다! 보관함 리스트에서 확인해 주세요.")
        if st.button("🔄 보관함 새로고침 (Refresh)", type="primary"):
            st.rerun()
            
    st.write("---")
    
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    report_files = [f for f in os.listdir("reports") if f.endswith(".md") and not f.endswith("_eval.md")]
    report_files.sort(key=lambda x: os.path.getmtime(os.path.join("reports", x)), reverse=True)
    
    if not report_files:
        st.info("아직 보관된 기획서가 없습니다. '기획안 생성기' 탭에서 첫 기획서를 생성해보세요!")
    else:
        for rf in report_files:
            import re
            # 1. 파일명 기반 직관적 네이밍 (파싱 오류 해결)
            cleaned_name = re.sub(r'(_\d+)?\.md$', '', rf)
            headline = cleaned_name.replace('_', ' ')
            display_title = headline
            
            # 2. 바깥쪽 삭제 버튼과 토글 박스를 나란히 배치 (접근성 개선)
            row_col1, row_col2 = st.columns([10, 1])
            
            with row_col2:
                # 상하 여백을 주어 버튼 위치 조정
                st.write("")
                if st.button("🗑️", key=f"del_out_{rf}", help="영구 삭제"):
                    for ext in ['.md', '.txt', '_eval.md', '.html', '.pptx']:
                        target = os.path.join("reports", rf.replace('.md', ext))
                        if os.path.exists(target):
                            os.remove(target)
                    st.rerun()
            
            with row_col1:
                with st.expander(f"📝 {headline}"):
                    
                    # MD 내용 읽기
                    with open(os.path.join("reports", rf), "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # TXT 내용 읽기
                    txt_rf = rf.replace('.md', '.txt')
                    ppt_content = ""
                    txt_path = os.path.join("reports", txt_rf)
                    if os.path.exists(txt_path):
                        with open(txt_path, "r", encoding="utf-8") as tf:
                            ppt_content = tf.read()
                    
                    # EVAL 내용 읽기
                    eval_rf = rf.replace('.md', '_eval.md')
                    eval_content = ""
                    eval_path = os.path.join("reports", eval_rf)
                    if os.path.exists(eval_path):
                        with open(eval_path, "r", encoding="utf-8") as ef:
                            eval_content = ef.read()
                    
                    # 탭으로 분리해서 보여주기
                    inner_tab1, inner_tab2, inner_tab3 = st.tabs(["📄 상세 기획서 (MD)", "💻 PPT 파싱 코드 (TXT)", "👩‍⚖️ 심사평가서 (MD)"])
                    with inner_tab1:
                        st.markdown(content)
                    with inner_tab2:
                        if ppt_content:
                            st.code(ppt_content, language="text")
                        else:
                            st.warning("이 버전은 PPT 파싱 코드가 생성되기 이전의 기록입니다.")
                    with inner_tab3:
                        if eval_content:
                            st.markdown(eval_content)
                        else:
                            st.warning("이 버전은 심사평가서가 생성되기 이전의 기록입니다.")
                    
                    # 버튼 영역
                    st.divider()
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button(
                            label=f"📥 기획서(MD) 다운로드",
                            data=content,
                            file_name=rf,
                            mime="text/markdown",
                            key=f"dl_{rf}"
                        )
                    with col_b:
                        render_source = ppt_content if ppt_content else content
                        html_rf = rf.replace('.md', '.html')
                        html_path = os.path.join("reports", html_rf)
                        st.markdown("##### 🎨 마스터 디자인 렌더링")
                        st.info("선택한 디자인 테마를 기반으로 슬라이드를 렌더링합니다.")
                        
                        import glob
                        preset_files = glob.glob("design_presets/*.md")
                        preset_names = [os.path.basename(f) for f in preset_files]
                        options = preset_names + ["🖼️ 새로운 레퍼런스 이미지 자동 추출"]
                        
                        if f"next_preset_{rf}" in st.session_state:
                            # 렌더링 전(위젯 생성 전)에 미리 session_state 업데이트
                            st.session_state[f"preset_{rf}"] = st.session_state[f"next_preset_{rf}"]
                            del st.session_state[f"next_preset_{rf}"]
                            
                        col_select, col_delete = st.columns([4, 1])
                        with col_select:
                            preset_option = st.selectbox(
                                "디자인 테마 선택",
                                options,
                                key=f"preset_{rf}"
                            )
                        with col_delete:
                            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                            if preset_option != "🖼️ 새로운 레퍼런스 이미지 자동 추출":
                                if st.button("🗑️ 삭제", key=f"del_preset_{rf}"):
                                    preset_path = os.path.join("design_presets", preset_option)
                                    if os.path.exists(preset_path):
                                        os.remove(preset_path)
                                        st.rerun()
                        
                        uploaded_img = None
                        if preset_option == "🖼️ 새로운 레퍼런스 이미지 자동 추출":
                            uploaded_img = st.file_uploader("레퍼런스 이미지 업로드 (JPG/PNG)", type=['png', 'jpg', 'jpeg'], key=f"img_{rf}")
                            if st.button("🧠 1단계: 레퍼런스 디자인 분석 및 룰셋 추출", type="primary", key=f"extract_{rf}"):
                                if uploaded_img:
                                    import base64
                                    ref_base64 = base64.b64encode(uploaded_img.read()).decode('utf-8')
                                    with st.spinner("Vision AI가 레퍼런스를 분석하고 컨셉을 추출 중입니다... (약 10초)"):
                                        import importlib
                                        import core.html_renderer
                                        importlib.reload(core.html_renderer)
                                        success, result = core.html_renderer.extract_design_preset(ref_base64)
                                        if success:
                                            st.session_state[f"next_preset_{rf}"] = result
                                            st.rerun()
                                        else:
                                            st.error(f"추출 실패: {result}")
                                else:
                                    st.warning("이미지를 먼저 업로드해주세요.")
                        else:
                            preset_path = os.path.join("design_presets", preset_option)
                            if os.path.exists(preset_path):
                                with st.expander("🛠️ 프리셋 튜닝 스튜디오 (상급자용)"):
                                    st.markdown("AI가 추출한 컨셉, 폰트, 컬러코드 등을 직접 확인하고 수정(Tuning)하세요.")
                                    with open(preset_path, "r", encoding="utf-8") as f:
                                        preset_content = f.read()
                                    
                                    edited_preset = st.text_area("Design Rules & Custom CSS", value=preset_content, height=400, key=f"edit_preset_{rf}")
                                    if st.button("💾 변경사항 저장", key=f"save_preset_{rf}"):
                                        with open(preset_path, "w", encoding="utf-8") as f:
                                            f.write(edited_preset)
                                        st.success("프리셋이 성공적으로 수정되었습니다! 아래 렌더링 버튼을 눌러 적용하세요.")
                                        
                            btn_label = "🔄 2단계: 디자인 룰셋 적용 렌더링" if os.path.exists(html_path) else "✨ 2단계: 완벽한 HTML로 시각화하기"
                            
                            if st.button(btn_label, type="primary", key=f"render_{rf}"):
                                selected_preset_file = preset_option
                                
                                with st.spinner("마스터 렌더링 파이프라인 가동 중... 디자인 룰셋 주입 및 코딩 중 (약 20초 소요)"):
                                    import importlib
                                    import core.html_renderer
                                    importlib.reload(core.html_renderer)
                                    from core.html_renderer import create_html_file
                                    
                                    try:
                                        success, message = create_html_file(render_source, html_path, headline, selected_preset_file, None)
                                        if success:
                                            st.success("HTML 코딩 및 렌더링 완료!")
                                        else:
                                            st.error(f"렌더링 실패: {message}")
                                    except Exception as e:
                                        st.error(f"오류 발생: {str(e)}")
                                    
                                if os.path.exists(html_path):
                                    with open(html_path, "r", encoding="utf-8") as hf:
                                        show_html_preview(hf.read())
                        if os.path.exists(html_path):
                            with open(html_path, "r", encoding="utf-8") as hf:
                                html_data = hf.read()
                            if st.button("👁️ 모달창에서 즉시 띄워보기", key=f"view_html_{rf}"):
                                show_html_preview(html_data)
                            st.download_button(label="📥 실제 HTML 다운로드", data=html_data, file_name=html_rf, mime="text/html", key=f"dl_html_btn_{rf}")

with tab3:
    st.markdown("### 📰 일일 트렌드 & 아트 인사이트")
    st.markdown("전 세계의 신선한 마케팅과 현대 예술 사례를 매일 하나씩 스캔하여 실무 적용 가능한 인사이트를 추출합니다.")
    
    col_t1, col_t2 = st.columns([1, 3])
    
    import time
    import core.trend_agent
    from core.trend_agent import get_all_trend_info, load_trend_report, fetch_daily_trend_report, delete_trend_report
    
    trend_data = get_all_trend_info()
    today_str = time.strftime('%Y-%m-%d')
    today_exists = any(t["date_str"] == today_str for t in trend_data)
    
    # 자동 발굴 로직 (오늘 날짜가 없으면 즉시 실행)
    if not today_exists:
        try:
            env_openai = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            if env_openai: os.environ["OPENAI_API_KEY"] = env_openai
            env_tavily = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", ""))
            if env_tavily: os.environ["TAVILY_API_KEY"] = env_tavily
            
            if os.getenv("OPENAI_API_KEY") and os.getenv("TAVILY_API_KEY"):
                with st.spinner("🌍 오늘의 글로벌 마케팅/예술 트렌드를 자동 수집하고 있습니다... (최초 1회 약 15초 소요)"):
                    fetch_daily_trend_report()
                    st.rerun()
        except:
            pass
            
    # 데이터 리로드
    trend_data = get_all_trend_info()
    
    if "selected_trend_id" not in st.session_state:
        st.session_state.selected_trend_id = trend_data[0]["file_id"] if trend_data else None
    
    with col_t1:
        st.markdown("#### 📅 리포트 보관함")
        
        if trend_data:
            # 커스텀 썸네일 리스트 뷰
            for item in trend_data:
                c1, c2 = st.columns([1, 2])
                with c1:
                    if item.get("image_url"):
                        st.image(item["image_url"], use_column_width=True)
                    else:
                        st.info("No Image")
                with c2:
                    if st.button(item["display"], key=f"btn_{item['file_id']}", use_container_width=True):
                        st.session_state.selected_trend_id = item["file_id"]
            
            # 개별 삭제 기능
            st.write("---")
            if st.session_state.selected_trend_id:
                if st.button("🗑️ 선택된 리포트 삭제", use_container_width=True):
                    delete_trend_report(st.session_state.selected_trend_id)
                    st.session_state.selected_trend_id = None
                    st.success("삭제되었습니다!")
                    st.rerun()
        else:
            st.write("아직 저장된 트렌드 리포트가 없습니다.")
            
        st.write("---")
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("🔄 전체 리포트 텍스트 전면 개조", use_container_width=True):
                with st.spinner("과거 리포트들을 새로운 구체적 팩트 기반(80/20)으로 전면 재작성 중입니다... (약 1분 소요)"):
                    import core.trend_agent
                    count = core.trend_agent.rewrite_all_reports_content()
                    st.success(f"{count}개의 리포트가 구체적인 팩트 중심으로 전면 개조되었습니다!")
                    st.rerun()
        with c_btn2:
            if st.button("🔥 트렌드 수동 재발굴", type="primary", use_container_width=True):
                try:
                    env_openai = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
                    if env_openai: os.environ["OPENAI_API_KEY"] = env_openai
                    env_tavily = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", ""))
                    if env_tavily: os.environ["TAVILY_API_KEY"] = env_tavily
                except:
                    pass
                    
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("OpenAI API Key가 설정되지 않았습니다.")
                elif not os.getenv("TAVILY_API_KEY"):
                    st.error("Tavily API Key가 설정되지 않았습니다.")
                else:
                    with st.spinner("🌍 전 세계 마케팅 & 예술 트렌드를 스캔 중입니다... (약 15초 소요)"):
                        try:
                            fetch_daily_trend_report()
                            st.success("오늘의 인사이트 재발굴 완료!")
                            # 새 리포트가 생기면 선택을 초기화하여 방금 생성한 것을 보게 함
                            st.session_state.selected_trend_id = None 
                            st.rerun()
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {str(e)}")
                        
    with col_t2:
        if st.session_state.selected_trend_id:
            report_content = load_trend_report(st.session_state.selected_trend_id)
            if report_content:
                st.markdown(report_content)
        else:
            st.info("좌측에서 트렌드를 선택해 주세요.")
