## 📛 Genre Name
[NAME: Bold_Modernist]

## 💡 Core Concept & Killer Points
- **메인 컨셉 (Main Concept):** 강렬한 색상과 대담한 타이포그래피를 통해 명확하고 직접적인 메시지를 전달.
- **킬러 포인트 (Killer Points):**
  1. 대조적인 컬러 블록 사용.
  2. 대형 산세리프 타이포그래피.
  3. 간결한 화살표와 선형 요소로 시각적 흐름 강조.

## 📐 Component Mapping Blueprint
1. **대조적 컬러 블록:** `.grid-2-col`과 `.bg-color-block`을 사용하여 각 슬라이드의 배경 색상을 설정.
2. **대형 타이포그래피:** `.text-massive`와 `.text-bold`를 조합하여 메시지를 강조.
3. **선형 요소:** `.arrow-line`과 `.step-indicator`를 사용하여 흐름을 시각적으로 표현.

## 📌 Design Rules
- **무드 & 페르소나:** 현대적이고 대담한 프레젠테이션.
- **동적 구글 폰트 (Dynamic Fonts):** `Bebas Neue` 폰트 사용. 
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
  ```
- **컬러 매핑:** 
  - 배경: #F5F5F5
  - 텍스트: #000000
  - 포인트 컬러: #FF00FF, #FFFF00, #FF4500
  - 테두리: #000000
- **타이포그래피 위계:** 
  - 헤드라인: `Bebas Neue`, sans-serif
  - 본문: `Arial`, sans-serif
  - 데이터(숫자): `Bebas Neue`, sans-serif
- **시그니처 디테일:** 컬러 블록 간의 간격과 화살표의 애니메이션.

## 🧩 Component & Blueprint Usage Guide
- **HTML 구조 예시:**
  ```html
  <div class="slide-page layout-color-block">
    <div class="color-block bg-pink">
      <div class="content-box">
        <h1 class="text-massive">START</h1>
        <div class="arrow-line"></div>
        <h2 class="text-massive">FINISH</h2>
      </div>
    </div>
  </div>
  ```

## 💻 Custom CSS
```css
/* 1. Dynamic Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

:root { 
  --bg: #F5F5F5; 
  --text: #000000; 
  --accent-pink: #FF00FF; 
  --accent-yellow: #FFFF00; 
  --accent-orange: #FF4500; 
  --border: #000000; 
}

body { 
  background: var(--bg); 
  color: var(--text); 
  font-family: 'Bebas Neue', sans-serif; 
}

h1, h2, h3 { 
  font-size: 3rem; 
  font-weight: bold; 
}

p, li { 
  word-break: keep-all; 
  font-size: 1rem; 
}

.arrow-line { 
  width: 100%; 
  height: 5px; 
  background-color: var(--text); 
  margin: 20px 0; 
}

.bg-color-block { 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  padding: 40px; 
}

.bg-pink { background-color: var(--accent-pink); }
.bg-yellow { background-color: var(--accent-yellow); }
.bg-orange { background-color: var(--accent-orange); }

.card { 
  background: transparent !important; 
  border: none !important; 
  box-shadow: none !important; 
  transition: all 0.3s ease; 
}

.card:hover { 
  transform: translateY(-5px); 
}

@keyframes fade-in-up { 
  from { opacity: 0; transform: translateY(20px); } 
  to { opacity: 1; transform: translateY(0); } 
}

.slide-page { 
  animation: fade-in-up 0.8s ease-out forwards; 
}
```