import os
import re

def extract_design_preset(ref_base64):
    """
    1단계: 레퍼런스 이미지에서 컨셉과 룰셋만 추출하여 파일로 저장합니다.
    """
    from langchain_core.messages import SystemMessage, HumanMessage
    import re, os
    from core.nodes import get_openai_llm
    llm = get_openai_llm()
    
    vision_sys = """You are an expert Art Director and Frontend Architect. 
당신은 최고급 UI 프레임워크를 다루는 Frontend Architect입니다. (Phase 4 Component Orchestrator)
시스템에는 이미 강력하고 완벽하게 동작하는 [High-End Component Library]가 탑재되어 있습니다. 
당신은 레퍼런스 이미지를 보고 직접 불안정한 CSS를 창조하는 대신, **시스템의 레고 블록(컴포넌트 클래스)들을 어떻게 조립하면 레퍼런스와 똑같아질지 매핑(Mapping)하는 역할**을 수행합니다.

Your output must be structured exactly as follows:

## 📛 Genre Name
이 장르를 완벽히 요약하는 2~3단어의 영문 뱀파이어 표기(예: `Minimal_Editorial`, `Neon_Cyberpunk`)를 다음 포맷으로 정확히 출력하세요:
[NAME: Your_Genre_Name]

## 💡 Core Concept & Killer Points (컨셉 및 핵심 포인트)
- **메인 컨셉 (Main Concept):** 이 레퍼런스가 전달하려는 핵심 감정과 시각적 메시지.
- **킬러 포인트 (Killer Points):** 이 디자인을 가장 돋보이게 만드는 3가지 조형적 특징 (예: 1. 화면을 가로지르는 사선 분할, 2. 비대칭 여백, 3. 극단적 타이포그래피 스케일).

## 📐 Component Mapping Blueprint (컴포넌트 매핑 및 테마 조립 가이드)
(매우 중요) CSS를 직접 짜서 레이아웃이 붕괴되는 것을 막기 위해, 시스템에 내장된 컴포넌트 클래스들(`.grid-2-col`, `.grid-asymmetric`, `.bg-diagonal`, `.glass-card`, `.brutal-card`, `.text-massive`, `.text-outline` 등)을 어떻게 조합해야 이 레퍼런스의 조형적 특징을 완벽하게 재현할 수 있는지 3가지 핵심 슬라이드 조립 가이드를 명시하세요.

## 📌 Design Rules (프론트엔드 조립 규칙)
- **무드 & 페르소나:** 레퍼런스의 디자인 장르 규명.
- **동적 구글 폰트 (Dynamic Fonts):** 완벽하게 어울리는 구글 폰트 조합과 CSS `@import url(...)` 명시.
- **컬러 매핑:** 배경, 텍스트, 포인트 컬러, 테두리 등 4코어 컬러 매핑.
- **타이포그래피 위계:** 헤드라인, 본문, 데이터(숫자) 폰트 지정.
- **시그니처 디테일:** 컬러 매트, 그림자, 필터 등 커스텀 CSS 규칙.

## 🧩 Component & Blueprint Usage Guide (HTML 조립 설명서)
(최우선 중요도) 당신이 `Layout Blueprints`와 `Custom CSS`에서 새롭게 정의한 커스텀 레이아웃 클래스들을 Text AI가 **어떻게 HTML DOM 구조로 엮어내야 하는지 완벽한 가이드라인과 태그 계층 구조**를 제공하세요.
- 예시: "`layout-diagonal`을 사용할 때는 반드시 `<div class='slide-page layout-diagonal'><div class='diagonal-bg'></div><div class='content-box'>...</div></div>` 구조로 작성해야 사선이 깨지지 않습니다."

## 💻 Custom CSS (렌더러 주입용)
```css
/* Provide valid CSS overriding the naked skeleton to completely reskin it into the reference genre. Do NOT redefine structural layouts like .slide-container. */
/* 1. Dynamic Google Fonts Import */
@import url('...'); /* 당신이 선택한 폰트의 실제 구글 폰트 주소를 넣으세요 */

:root { --bg: ...; --text: ...; --accent: ...; --border: ...; }
body { background: var(--bg); color: var(--text); font-family: ...; }
h1, h2, h3 { ... }
p, li { word-break: keep-all; ... }
.huge-number { ... }
.fact-label { ... }
/* 이미지 필터링 필수 부여 */
.brutal-img, .img-hero, .img-float-right, .circle-img { filter: ...; border-radius: ...; }
/* 장식 요소 및 마이크로 인터랙션 모션 */
.marker-underline { ... }
.hand-drawn-circle { ... }
.card { background: transparent !important; border: none !important; box-shadow: none !important; transition: all 0.3s ease; }
.card:hover { transform: translateY(-5px); }
@keyframes fade-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.slide-page { animation: fade-in-up 0.8s ease-out forwards; }
```"""
    vision_user = "제공된 레퍼런스 이미지의 디자인 룰(구조, 컬러, 폰트)을 정밀 분석하고, 프레임워크(Genre Name, Core Concept, Layout Blueprints, Design Rules, Component Usage Guide, Custom CSS)에 맞게 완벽히 작성해 줘."
    
    vision_msgs = [
        SystemMessage(content=vision_sys),
        HumanMessage(content=[
            {"type": "text", "text": vision_user},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{ref_base64}"}}
        ])
    ]
    
    try:
        vis_resp = llm.invoke(vision_msgs).content
        name_match = re.search(r"\[NAME:\s*(.+?)\]", vis_resp)
        preset_name = name_match.group(1).strip() if name_match else "Auto_Extract"
        preset_name = re.sub(r'[^a-zA-Z0-9_]', '_', preset_name)
        
        filename = f"{preset_name}.md"
        base_dir = os.path.dirname(os.path.dirname(__file__))
        preset_filepath = os.path.join(base_dir, "design_presets", filename)
        with open(preset_filepath, "w", encoding="utf-8") as pf:
            pf.write(vis_resp)
        return True, filename
    except Exception as e:
        return False, str(e)


def create_html_file(ppt_content, filepath, brief_input, selected_preset_file=None, ref_base64=None):
    from core.nodes import get_openai_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    import re
    import os
    
    naked_skeleton = """<!DOCTYPE html>
<html lang="ko" class="theme-light">
<head>
  <meta charset="UTF-8">
  <title>YOUR TITLE HERE</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Noto+Sans+KR:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <script>Chart.defaults.animation = false;</script>
  <style>
    /* DESIGN TOKENS & THEME SYSTEM */
    :root {
      --bg: #F8FAF9; --surface: #FFFFFF; --text: #111111; --text-secondary: #555555;
      --accent: #2563EB; --border: rgba(0,0,0,0.08); --positive: #10B981; --negative: #EF4444;
      --glass-bg: rgba(255, 255, 255, 0.7); --glass-border: rgba(255, 255, 255, 0.5);
    }
    html.theme-dark {
      --bg: #0A0A0A; --surface: #1A1A1A; --text: #EDEDED; --text-secondary: #A1A1AA;
      --accent: #3B82F6; --border: rgba(255,255,255,0.1);
      --glass-bg: rgba(20, 20, 20, 0.6); --glass-border: rgba(255, 255, 255, 0.08);
    }
    
    /* NAKED RESET */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Noto Sans KR', 'Inter', sans-serif; background: #000; color: var(--text); line-height: 1.6; }
    img { max-width: 100%; display: block; }
    
    /* EXPORT BUTTON */
    #export-controls { position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; gap: 8px; }
    .export-btn { background: var(--text); color: var(--bg); border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: transform 0.2s; font-family: 'Noto Sans KR', sans-serif;}
    .export-btn:hover { transform: translateY(-2px); }

    /* CORE STRUCTURAL CSS (SINGLE-SCREEN POSTER LAYOUT) */
    .slide-container { display: flex; flex-direction: column; gap: 40px; padding: 40px; background: #000; align-items: center; }
    .slide-page { 
      width: 1920px; height: 1080px; /* 16:9 뷰포트 고정 */
      padding: 80px 100px; position: relative; overflow: hidden; 
      display: flex; flex-direction: column; justify-content: space-between;
      background: var(--bg); 
    }

    /* TYPOGRAPHY HIERARCHY */
    h1 { font-size: 4rem; font-weight: 800; line-height: 1.2; letter-spacing: -0.03em; margin-bottom: 24px; }
    h2 { font-size: 2.5rem; font-weight: 700; line-height: 1.3; letter-spacing: -0.02em; margin-bottom: 16px; }
    h3 { font-size: 1.5rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
    p, li { font-size: 1.125rem; word-break: keep-all; color: var(--text); }
    .text-massive { font-size: 160px; font-weight: 900; line-height: 1; letter-spacing: -0.05em; margin:0; padding:0; }
    .text-outline { color: transparent; -webkit-text-stroke: 2px var(--text); }
    .text-gradient { background: linear-gradient(90deg, var(--accent), var(--text)); -webkit-background-clip: text; color: transparent; }
    .fact-label { font-size: 1.25rem; font-weight: 600; color: var(--accent); letter-spacing: 0.1em; text-transform: uppercase; }

    /* LAYOUT COMPONENTS */
    .grid-2-col { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; flex: 1; }
    .grid-3-col { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; }
    .grid-asymmetric { display: grid; grid-template-columns: 2fr 1fr; gap: 64px; align-items: center; flex: 1; }
    .content-layer { position: relative; z-index: 10; width: 100%; height: 100%; display: flex; flex-direction: column; flex: 1; justify-content: center; }
    .flex-center { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
    
    /* AESTHETICS & BACKGROUNDS */
    .bg-diagonal { position: absolute; inset: 0; background: var(--surface); clip-path: polygon(0 0, 100% 0, 100% 70%, 0 100%); z-index: 0; }
    .bg-circle { position: absolute; width: 800px; height: 800px; border-radius: 50%; background: var(--accent); opacity: 0.05; top: -100px; right: -100px; z-index: 0; }
    .bg-gradient { position: absolute; inset: 0; background: linear-gradient(135deg, var(--bg) 0%, var(--surface) 100%); z-index: 0; }
    
    .glass-card { 
      background: var(--glass-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); 
      border: 1px solid var(--glass-border); border-radius: 16px; padding: 48px; 
      box-shadow: 0 8px 32px rgba(0,0,0,0.05); 
    }
    .brutal-card { background: var(--surface); border: 2px solid var(--text); padding: 48px; border-radius: 8px; box-shadow: 12px 12px 0px var(--border); }
    .chart-container { height: 400px; padding: 40px; border-radius: 12px; background: var(--surface); border: 1px solid var(--border); box-shadow: 0 4px 24px rgba(0,0,0,0.02); }
    
    .img-rounded { border-radius: 16px; object-fit: cover; width: 100%; height: 100%; }
    
    /* MICRO ANIMATIONS */
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
    .animate { animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; }
    .delay-1 { animation-delay: 0.1s; } .delay-2 { animation-delay: 0.2s; } .delay-3 { animation-delay: 0.3s; }
  </style>
  <style id="dynamic-css">
    /* VISION_CSS_HERE */
  </style>
</head>
<body>
  <div id="capture-area" class="slide-container">
    <!-- YOUR CONTENT HERE -->
  </div>
  <div id="export-controls">
    <button class="export-btn" onclick="exportJPEG()">📸 JPEG로 저장</button>
  </div>
  <script>
    function exportJPEG() {
      const node = document.getElementById('capture-area');
      const btn = document.querySelector('.export-btn');
      btn.innerText = "⏳ 렌더링 중...";
      htmlToImage.toJpeg(node, { quality: 0.95, backgroundColor: '#000' })
        .then(function (dataUrl) {
          var link = document.createElement('a'); link.download = 'presentation_export.jpg'; link.href = dataUrl; link.click();
          btn.innerText = "📸 JPEG로 저장";
        }).catch(function (error) { console.error('Error!', error); btn.innerText = "❌ 오류 발생"; });
    }
    
    function getChartColors() {
      var s = getComputedStyle(document.documentElement);
      return {
        text: s.getPropertyValue('--text').trim(),
        textSecondary: s.getPropertyValue('--text-secondary').trim(),
        border: s.getPropertyValue('--border').trim(),
      };
    }
  </script>
</body>
</html>"""

    skeleton_content = naked_skeleton
    llm = get_openai_llm()
    custom_css = ""
    design_rules = ""

    # Preset Selection
    if selected_preset_file and selected_preset_file != "None":
        base_dir = os.path.dirname(os.path.dirname(__file__))
        design_system_path = os.path.join(base_dir, "design_presets", selected_preset_file)
        try:
            if os.path.exists(design_system_path):
                with open(design_system_path, "r", encoding="utf-8") as f:
                    design_content = f.read()
                    
                css_match = re.search(r"```css\s*(.*?)\s*```", design_content, re.DOTALL | re.IGNORECASE)
                if css_match:
                    custom_css = css_match.group(1)
                else:
                    custom_css = "/* CSS 추출 실패 */"
                design_rules = re.sub(r"```css\s*.*?\s*```", "", design_content, flags=re.DOTALL | re.IGNORECASE).strip()
        except Exception as e:
            print(f"[Design System Load Error]: {e}")
            pass

    # STEP 2: Text AI (HTML Builder)
    system_instruction = f"""당신은 세계 최고 에이전시의 프리젠테이션 디렉터입니다. 당신의 지상 과제는 '원문을 100% 보존하면서, 최신 AI 하이엔드 디자인 방법론(글래스모피즘, 극단적 타이포그래피 스케일, 마이크로 애니메이션)을 적용해 에이전시급의 완벽한 단일 HTML 프리젠테이션을 빚어내는 것'입니다.

[🎯 전문가 수준 디자인 리듬의 5대 원칙]
1. **단일 뷰포트 고정 (Single-Screen Poster):** 각 슬라이드(`<div class="slide-page">`)는 가로 1920px, 세로 1080px 비율로 고정되어 있으며 `overflow: hidden` 처리되어 있습니다. 스크롤이 생기지 않도록 `flex: 1`과 `justify-content: space-between`을 활용해 슬라이드 캔버스를 여백 없이 꽉 차게 활용하세요.
2. **강조의 디테일 (정밀 연출 - Emphasis):** 내용 중 가장 핵심이 되는 메세지나 팩트(Data)를 스스로 추출하여, 화면 중앙에 초거대 타이포그래피(`.text-massive`, 160px)와 팩트 라벨(`.fact-label`)을 압도적으로 배치하세요.
3. **절제의 디테일 (글래스모피즘과 여백 - Restraint):** '비전'이나 '인사이트' 구간에서는 억지로 화면을 채우지 마세요. 스칸디나비아 미술처럼 화면의 70% 이상을 차가운 여백으로 비워두고, 부드럽고 투명한 글래스 카드(`.glass-card`)만 얹어 우아하게 떠 있는 듯한 레이어(Layer) 감각을 부여하세요.
4. **마이크로 애니메이션과 리듬:** 각 요소(카드, 텍스트)에는 `.animate`, `.delay-1`, `.delay-2` 클래스를 조합하여 화면 등장 시 폭포수처럼 부드럽게 나타나게 하세요.
5. **Chart.js 완벽 연동:** 기획서에 통계 수치가 있다면 `Chart.js`를 사용해 고급스러운 차트를 렌더링하세요. 차트는 반드시 `<div class="chart-container"><canvas id="..."></canvas></div>` 구조로 감싸고 JS 옵션에 `maintainAspectRatio: false`를 부여하세요.
6. **고해상도 이미지 프롬프트 (Pollinations AI):** `<img src="https://image.pollinations.ai/prompt/{{English_Prompt}}?width=1600&height=900&nologo=true" class="img-rounded" alt="배경">`. `{{English_Prompt}}`는 5단계(Subject, Action, Background, Lighting, Mood)로 영작하되, **[Mood] 파라미터에 위에서 정한 리듬(예: aggressive dynamic vs scandinavian minimalist calm)을 반드시 반영**하세요.

[✨ Few-Shot 예시: 디테일을 통한 강조와 절제란 이런 것이다]
입력 마크다운:
"## 비전: 여백의 갓생
우리는 더 이상 빽빽한 시간표로 청년들을 옭아매지 않습니다. 데이터에 따르면 89%가 '디지털 디톡스를 통한 완전한 침묵'을 원하고 있습니다."

프리젠테이션 디렉터의 HTML (팩트의 '강조'와 비전의 '절제'를 슬라이드 분할로 리듬감 있게 연출):
<!-- 슬라이드 1: 팩트 (강조의 디테일 - 초거대 타이포그래피 정밀 연출) -->
<div class="slide-page animate">
  <div class="bg-diagonal"></div>
  <div class="content-layer grid-asymmetric">
    <div class="flex-center animate delay-1">
      <h3 class="text-massive">89%</h3>
      <span class="fact-label">DIGITAL DETOX</span>
    </div>
    <div class="glass-card flex-center animate delay-2">
      <h2>데이터에 따르면 압도적인 수의 타겟이 '디지털 디톡스를 통한 완전한 침묵'을 원하고 있습니다.</h2>
    </div>
  </div>
</div>

<!-- 슬라이드 2: 비전 (절제의 디테일 - 여백 70% 이상, 차갑고 우아한 무드) -->
<div class="slide-page animate">
  <div class="bg-gradient"></div>
  <div class="content-layer flex-center">
    <div class="glass-card animate delay-2" style="max-width: 800px;">
      <h3 style="letter-spacing: 0.2em; opacity: 0.8;">THE RIGHT TO DO NOTHING</h3>
      <h2 style="margin-top: 24px;">여백의 갓생</h2>
      <p style="margin-top: 16px;">우리는 더 이상 빽빽한 시간표로 청년들을 옭아매지 않습니다. 그들이 진정 원하는 것은 아무것도 하지 않을 수 있는 권리입니다.</p>
    </div>
  </div>
</div>
"""
    if custom_css:
        system_instruction += f"""
[동적 디자인 룰셋 적용 지시]
다음은 Art Director가 레퍼런스 이미지를 분석하여 추출한 이 프로젝트만의 '고유 디자인 규칙'과 '커스텀 CSS'입니다.
당신은 HTML을 구성할 때 반드시 이 <디자인 규칙>을 100% 반영하여 클래스와 레이아웃을 짜야 하며, 아래 <커스텀 CSS>를 뼈대의 <head> 태그 안 <style>에 추가하여 디자인을 완벽히 덮어씌워야 합니다.

<디자인 규칙>
{design_rules}

<커스텀 CSS>
{custom_css}
"""

    system_instruction += f"\n[Skeleton HTML]\n{skeleton_content}\n"

    user_text = f"다음은 작성된 기획서 내용입니다. 위에서 전달받은 디자인 룰셋과 CSS를 뼈대에 주입하고, 기획서의 내용을 가장 아름답게 시각화한 단일 HTML을 코딩해 주세요.\n\n[기획서 제목]: {brief_input}\n\n[기획서 원문]:\n{ppt_content}"
    
    text_msgs = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_text)
    ]
    
    try:
        response = llm.invoke(text_msgs)
        content = response.content.strip()
        
        # 정규식을 이용해 순수 HTML 코드만 추출
        html_match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
        if html_match:
            content = html_match.group(1)
        else:
            doc_match = re.search(r"(<!DOCTYPE html>.*</html>)", content, re.DOTALL | re.IGNORECASE)
            if doc_match:
                content = doc_match.group(1)
            else:
                content = content.replace("```html", "").replace("```", "").strip()
        
        content = content.strip()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True, "Success"
    except Exception as e:
        error_html = f"<html><body><h1>HTML 렌더링 실패</h1><p>{e}</p></body></html>"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(error_html)
        return False, str(e)
