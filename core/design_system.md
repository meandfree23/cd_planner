# 🎨 Current Design System (Active)

**Style Name:** Vivid Brutalism (Kim Seong-min Coffee / MZ Targeting)

## 📌 Design Rules (프론트엔드 조립 규칙)
- **전체적인 느낌:** MZ세대를 타겟으로 한 힙하고 엣지 있는 브루탈리즘(Brutalism) 스타일. 군더더기 없는 흑백 배경에 강렬한 블루로 시선을 사로잡습니다.
- **컬러 팔레트:** 오직 화이트(배경), 블랙(텍스트 및 굵은 선), 비비드 블루(포인트 컬러) 3가지만 사용합니다.
- **타이포그래피:** 헤드라인은 매우 굵고 거대한 산세리프체(Sans-serif)를 사용하여 시각적 타격을 줍니다. 서브 텍스트나 데이터, 라벨링은 코딩 화면처럼 차가운 모노스페이스(Monospace) 폰트를 사용하여 대비를 줍니다.
- **이미지 연출:** 모든 이미지는 완벽한 흑백(Grayscale 100%)으로 처리하여 차갑고 힙한 느낌을 유지합니다.
- **장식 요소 (Decorations):** 비비드 블루 컬러를 활용한 손그림 느낌의 원(Circle), 밑줄(Underline), 화살표 등을 텍스트 강조용으로 적극 활용하세요.
- **레이아웃 구조 (A4 슬라이드):**
  - 기획서 원문을 그대로 쏟아내지 말고, 각 슬라이드의 메인 메시지에 맞게 **카피라이팅 위주의 짧은 문구**로 반드시 요약/재작성하세요.
  - 슬라이드 구성은 `.layout-hero`, `.layout-headline`, `.layout-harmony`, `.layout-stats` 중 하나를 선택해 변별력을 줍니다.

## 💻 Custom CSS (렌더러 주입용)
```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+KR:wght@400;800;900&display=swap');

:root {
  --bg: #FFFFFF;
  --text: #000000;
  --accent: #0022FF; /* Vivid Blue */
  --border: #000000;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Noto Sans KR', sans-serif;
  letter-spacing: -0.03em;
}

/* Typography Hierarchy */
h1, h2, h3, .huge-number {
  font-family: 'Noto Sans KR', sans-serif;
  font-weight: 900;
  color: var(--text);
  text-transform: uppercase;
  line-height: 1.1;
  word-break: keep-all;
}

h1 { font-size: 4.5rem; margin-bottom: 30px; letter-spacing: -0.05em; }
h2 { font-size: 3.5rem; margin-bottom: 24px; border-bottom: 4px solid var(--text); padding-bottom: 10px; display: inline-block; }
h3 { font-size: 1.8rem; margin-bottom: 16px; font-weight: 800; }

p, li, .fact-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text);
  font-weight: 400;
}

/* A4 Landscape Slide Container */
.slide-container {
  display: flex;
  flex-direction: column;
  gap: 80px;
  padding: 40px;
  background: #F0F0F0;
  align-items: center;
}

.slide-page {
  background: var(--bg);
  width: 100%;
  max-width: 1414px;
  aspect-ratio: 1.414 / 1;
  padding: 80px 100px;
  border: 2px solid var(--text); /* 브루탈리즘 테두리 */
  box-shadow: 12px 12px 0px var(--accent); /* 비비드 블루 그림자 */
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 4 Distinct Layout Variations */
.layout-headline { justify-content: center; align-items: flex-start; }
.layout-headline h2 { font-size: 5rem; width: 90%; margin-bottom: 40px; border: none; }
.layout-headline p { font-size: 1.2rem; width: 70%; border-left: 4px solid var(--accent); padding-left: 20px; }

.layout-hero { padding: 0; justify-content: center; align-items: center; text-align: center; }
.layout-hero .img-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; filter: grayscale(100%); z-index: 1; }
.layout-hero .overlay { position: relative; z-index: 2; background: var(--bg); padding: 40px 60px; border: 4px solid var(--text); box-shadow: 8px 8px 0px var(--accent); }
.layout-hero h2 { font-size: 4rem; margin-bottom: 0; border: none; padding: 0; }

.layout-harmony { display: grid; grid-template-columns: 1fr 1.2fr; gap: 80px; align-items: center; height: 100%; }
.layout-harmony .img-side { width: 100%; height: 90%; object-fit: cover; filter: grayscale(100%); border: 2px solid var(--text); }

.layout-stats { justify-content: center; }
.layout-stats .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; margin-top: 60px; }
.layout-stats .stats-box { border-top: 4px solid var(--accent); padding-top: 20px; }

/* Visual & Decor Elements */
.brutal-img, .img-hero, .img-float-right {
  filter: grayscale(100%) !important;
  border: 2px solid var(--text);
}
.img-hero { width: 100%; height: 50vh; object-fit: cover; margin-bottom: 40px; }
.img-float-right { float: right; width: 45%; margin: 0 0 40px 40px; object-fit: cover; }
.circle-img { border-radius: 50%; aspect-ratio: 1/1; object-fit: cover; filter: grayscale(100%); border: 2px solid var(--text); }

/* Decoration Classes */
.marker-underline {
  background: linear-gradient(180deg, transparent 60%, var(--accent) 60%);
  padding: 0 4px;
}
.hand-drawn-circle {
  position: relative;
  display: inline-block;
  z-index: 1;
}
.hand-drawn-circle::before {
  content: ''; position: absolute; top: -5px; left: -10px; right: -10px; bottom: -5px;
  border: 3px solid var(--accent); border-radius: 50% 40% 60% 40% / 40% 60% 40% 50%;
  z-index: -1; transform: rotate(-2deg);
}

/* Artbook Typography */
.huge-number { font-size: 6rem; color: var(--accent); letter-spacing: -0.05em; }
.fact-label { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text); }

.card { background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; }
```
