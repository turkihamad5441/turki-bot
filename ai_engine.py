import requests
import urllib.parse

def get_ai_reply(prompt, system_prompt="أنت مساعد ذكي في بوت تركي للتنزيلات. أجب باللغة العربية بأسلوب ودود ومختصر."):
    try:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "model": "openai"
        }
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code == 200: return response.text
        return "عذراً، حدث خطأ."
    except:
        return "عذراً، الذكاء الاصطناعي غير متاح حالياً."

def generate_auto_adhkar():
    prompt = "اكتب ذكراً إسلامياً قصيراً جداً، ودعاءً مأثوراً قصيراً، مع إيموجيات إسلامية مناسبة. اجعل النص جاهز للإرسال في تيليجرام."
    return get_ai_reply(prompt, system_prompt="أنت مساعد إسلامي يكتب أذكار وأدعية قصيرة ومؤثرة.")

def generate_ai_image(prompt):
    try:
        encoded = urllib.parse.quote(prompt)
        return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
    except:
        return None
