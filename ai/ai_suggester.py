import os
from typing import List, Dict

PROVIDER = os.getenv("AI_PROVIDER", "openai")

def build_technical_prompt(signals: List[Dict]) -> str:
    """
    Monta um prompt detalhado para análise técnica, incluindo todos os dados do sinal,
    além de sentimento e volume anômalo.
    Garante que a resposta seja apenas os símbolos das duas moedas sugeridas.
    """
    details = "\n".join(
        f"{s['symbol']}: Entrada {s['entry_price']:.4f}, Stop {s['stop_loss']:.4f}, Alvo {s['take_profit']:.4f}, "
        f"Volume Anômalo: {s.get('anomalous_volume', False)}, Sentimento: {s.get('sentiment', 'neutro')}"
        for s in signals
    )
    prompt = (
        "Você é um analista técnico experiente e objetivo.\n"
        "Considere os seguintes sinais de short fornecidos por um screener automático:\n"
        f"{details}\n"
        "Analise e compare esses ativos baseando-se nos dados fornecidos "
        "(entrada, stop, alvo, volume anômalo, sentimento).\n"
        "Escolha **exatamente dois** ativos que oferecem o melhor potencial de trade para short "
        "neste momento, considerando:\n"
        "- Relação risco/retorno\n"
        "- Proximidade do stop\n"
        "- Potencial de queda e forças vindas de fatores externos\n"
        "FAÇA toda a análise mentalmente, mas **após decidir**, responda **SOMENTE** com os símbolos "
        "dos dois ativos, separados por vírgula, sem texto adicional. "
        "Exemplo de resposta: BTCUSDT,ETHUSDT"
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
                {"role": "system", "content": "Auxilie na escolha dos dois melhores ativos para short."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=20,  # deve caber dois tickers
        )
        text = resp.choices[0].message.content.strip()
        # Extrai até 2 símbolos, limpando espaços e quebras
        parts = [t.strip() for t in text.replace("\n", "").split(",") if t.strip()]
        return parts[:2]

elif PROVIDER == "gemini":
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    gemini = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.7}
    )

    def suggest_best_coin(signals: List[Dict]) -> List[str]:
        prompt = build_technical_prompt(signals)
        response = gemini.generate_content(prompt)
        text = ""
        if hasattr(response, "text"):
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            text = response.candidates[0].content.parts[0].text
        parts = [t.strip() for t in text.replace("\n", "").split(",") if t.strip()]
        return parts[:2]

else:
    from transformers import pipeline, set_seed
    _gen = pipeline("text-generation", model="EleutherAI/gpt-neo-125M")
    set_seed(42)

    def suggest_best_coins(signals: List[Dict]) -> List[str]:
        prompt = build_technical_prompt(signals)
        out = _gen(prompt, max_length=30, do_sample=True, temperature=0.7)[0]["generated_text"]
        # remove o prompt e pegue rest
        generated = out.replace(prompt, "").strip()
        parts = [t.strip() for t in generated.replace("\n", "").split(",") if t.strip()]
        return parts[:2]
