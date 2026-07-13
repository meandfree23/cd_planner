import os

print("="*50)
print("🔑 AI Creative Director - API Key Setup 🔑")
print("="*50)
print("발급받으신 API 키를 터미널에 붙여넣고 엔터(Enter)를 누르세요.")
print("(입력을 건너뛰려면 그냥 엔터를 치시면 됩니다.)\n")

openai_key = input("▶ OpenAI API Key (sk-... 등으로 시작) : ").strip()
gemini_key = input("▶ Google Gemini API Key (AIza... 등으로 시작) : ").strip()
tavily_key = input("▶ Tavily API Key (tvly-... 등으로 시작, 없으면 엔터) : ").strip()

env_content = f"""# OpenAI API Key (분석 및 기획서 작성에 사용)
OPENAI_API_KEY={openai_key if openai_key else 'your_openai_api_key_here'}

# Google Gemini API Key (창의적 아이디어 발상에 사용)
GOOGLE_API_KEY={gemini_key if gemini_key else 'your_gemini_api_key_here'}

# Tavily API Key (딥리서치 용도)
TAVILY_API_KEY={tavily_key if tavily_key else 'your_tavily_api_key_here'}
"""

with open(".env", "w", encoding="utf-8") as f:
    f.write(env_content)

print("\n" + "="*50)
print("✅ 성공! 입력하신 API 키가 완벽하게 저장되었습니다.")
print("이제 웹 화면(http://localhost:8501)을 새로고침 하시면 키가 영구적으로 자동 반영됩니다.")
print("="*50)
