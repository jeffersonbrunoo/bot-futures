import os
from typing import List, Dict
from config.settings import NEWS_LOOKBACK_DAYS, NEWS_PAGE_SIZE

PROVIDER = os.getenv("AI_PROVIDER", "openai")


def build_technical_prompt(signals: List[Dict]) -> str:
    details = []
    for s in signals:
        details.append(
            f"{s['symbol']}: Entrada {s['entry_price']:.4f}, Stop {s['stop_loss']:.4f}, "
            f"Alvo {s['take_profit']:.4f}, Volume Anômalo: {s.get('anomalous_volume', False)} "
            f"(z={s.get('anomalous_volume_z',0)}), Sentimento: {s.get('sentiment','neutro')}, "
            f"Notícias: {s.get('news_count',0)} artigos"
        )
    prompt = (
        "Você é um analista técnico experiente e objetivo.\n"
        f"Considere os sinais de short a seguir com fatores externos nos últimos {NEWS_LOOKBACK_DAYS} dia(s) (até {NEWS_PAGE_SIZE} artigos por símbolo):\n"
        + "\n".join(details) + "\n"
        "Analise entrada, stop, alvo, volume anômalo e sentimento de notícias. "
        "Escolha **exatamente dois** ativos com melhor potencial de short, considerando relação risco/retorno, proximidade do stop e força das notícias.\n"
        "Responda **SOMENTE** com os símbolos, separados por vírgula, sem texto adicional."
    )
    return prompt

if PROVIDER == "openai":
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    def suggest_best_coins(signals: List[Dict]) -> List[str]:
        prompt = build_technical_prompt(signals)
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Você sugere os dois melhores ativos para short."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=50,
        )
        text = resp.choices[0].message.content.strip()
        parts = [t.strip() for t in text.replace("\n", "").split(",") if t.strip()]
        return parts[:2]

elif PROVIDER == "gemini":
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    gemini = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.7}
    )

    def suggest_best_coins(signals: List[Dict]) -> List[str]:
        prompt = build_technical_prompt(signals)
        # Usar generate_content no SDK do Gemini
        response = gemini.generate_content(prompt)
        # Extrai texto da resposta
        if hasattr(response, "text") and response.text:
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            # .candidates[0].content.parts[0].text
            text = response.candidates[0].content.parts[0].text
        else:
            text = ""
        parts = [t.strip() for t in text.replace("\n", "").split(",") if t.strip()]
        return parts[:2]

else:
    from transformers import pipeline, set_seed
    _gen = pipeline("text-generation", model="EleutherAI/gpt-neo-125M")
    set_seed(42)

    def suggest_best_coins(signals: List[Dict]) -> List[str]:
        prompt = build_technical_prompt(signals)
        out = _gen(prompt, max_length=50, do_sample=True, temperature=0.7)[0]["generated_text"]
        # remove prompt do retorno
        generated = out.replace(prompt, "").strip()
        parts = [t.strip() for t in generated.replace("\n", "").split(",") if t.strip()]
        return parts[:2]

# Alias para compatibilidade com chamadas anteriores
suggest_best_coin = suggest_best_coins
