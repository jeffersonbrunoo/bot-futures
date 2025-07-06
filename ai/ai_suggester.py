import os
from typing import List, Dict

PROVIDER = os.getenv("AI_PROVIDER", "openai")

def build_technical_prompt(signals: List[Dict]) -> str:
    """
    Monta um prompt detalhado para análise técnica, incluindo todos os dados do sinal,
    além de sentimento e volume anômalo.
    Garante que a resposta seja apenas o símbolo da moeda sugerida.
    """
    details = "\n".join(
        f"{s["symbol"]}: Entrada {s["entry_price"]:.4f}, Stop {s["stop_loss"]:.4f}, Alvo {s["take_profit"]:.4f}, "
        f"Volume Anômalo: {s.get("anomalous_volume", False)}, Sentimento: {s.get("sentiment", "neutro")}"
        for s in signals
    )
    prompt = (
        "Você é um analista técnico experiente e objetivo.\n"
        "Considere os seguintes sinais de short fornecidos por um screener automático:\n"
        f"{details}\n"
        "Analise e compare esses ativos baseando-se nos dados fornecidos (entrada, stop, alvo, volume anômalo, sentimento). "
        "Escolha **apenas um** ativo que oferece o melhor potencial de trade para short neste momento, considerando:\n"
        "- Relação risco/retorno (distância entre entrada, stop e alvo)\n"
        "- Proximidade do stop\n"
        "- Potencial de queda e qualquer detalhe técnico notável do setup\n"
        "- **Fatores externos:** Se o volume for anômalo (True) e o sentimento for negativo, isso pode indicar um sinal mais forte para short.\n"
        "FAÇA toda a análise técnica mentalmente, mas **após decidir**, responda SOMENTE com o símbolo do ativo escolhido (ex: BTCUSDT), nada mais. "
        "Não escreva explicação, justificativa, motivo, frase, saudação ou texto adicional. "
        "Sua resposta final deve conter apenas o símbolo, exatamente como no exemplo: BTCUSDT"
    )
    return prompt

if PROVIDER == "openai":
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    def suggest_best_coin(signals: List[Dict]) -> str:
        prompt = build_technical_prompt(signals)
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Auxilie na escolha do melhor ativo para short, de forma objetiva e técnica. Só retorne o símbolo final."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=10,  # Só precisa de 1 símbolo/ticker
        )
        return resp.choices[0].message.content.strip().split()[0]  # Garante apenas o ticker

elif PROVIDER == "gemini":
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    gemini = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.7}
    )

    def suggest_best_coin(signals: List[Dict]) -> str:
        prompt = build_technical_prompt(signals)
        response = gemini.generate_content(prompt)
        # Extrai só o ticker, mesmo que a IA ignore a instrução
        if hasattr(response, "text"):
            return response.text.strip().split()[0]
        if hasattr(response, "candidates") and hasattr(response.candidates[0], "content"):
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                return parts[0].text.strip().split()[0]
        return str(response).strip().split()[0]

else:
    from transformers import pipeline, set_seed
    _gen = pipeline("text-generation", model="EleutherAI/gpt-neo-125M")
    set_seed(42)

    def suggest_best_coin(signals: List[Dict]) -> str:
        prompt = build_technical_prompt(signals)
        out = _gen(prompt, max_length=20, do_sample=True, temperature=0.7)[0]["generated_text"]
        return out.replace(prompt, "").strip().split()[0]


