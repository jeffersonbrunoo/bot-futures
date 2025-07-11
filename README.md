# 🤖 BOT TECH + IA – Screener de Sinais para Futuros (Cripto)

Este projeto é um **screener** para contratos **futuros** perpétuos na MEXC, combinando **análise técnica tradicional** com **inteligência artificial** para filtrar e notificar os melhores setups de entrada no mercado.

---

## 🚀 Visão Geral

O bot realiza uma varredura periódica nos pares disponíveis na exchange **MEXC** , aplicando critérios rigorosos como:

- Liquidez mínima
- Indicadores técnicos (EMA, RSI, MACD, Volume)
- Validação por IA (modelo generativo)
- Filtros de volatilidade e contexto de mercado
- Fatores externos

Ao identificar um **setup de venda (SHORT)** com alta probabilidade, o bot envia o sinal diretamente para o Telegram do usuário.

---

## 🧠 Estrutura do Projeto

```
📦 BOT-FUTURES/
├── __pycache__/
├── .pytest_cache/
├── ai/
│   ├── __pycache__/
│   ├── __init__.py
│   └── ai_suggester.py
├── config/
├── external_data/
├── mexc/
├── notifier/
├── reports/
│   ├── __pycache__/
│   ├── daily/
│   └── performance.py
├── scheduler/
│   ├── __pycache__/
│   ├── __init__.py
│   └── job_scheduler.py
├── screener/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── external_factors_evaluator.py
│   ├── filter_engine.py
│   ├── liquidity_filter.py
│   ├── screener_core.py
│   └── signal_generator.py
```

- `filters/`: lógica de filtragem por análise técnica
- `screener/`: cálculo de RSI, MACD, EMAs, Volume, Fatores Externos
- `ai/`: integração com modelo IA para validação dos sinais
- `notifier/`: envio automático dos sinais para Telegram
- `scheduler/`: agenda execuções recorrentes (ex: a cada 60 minutos)

---

## 📊 Indicadores Técnicos Utilizados

- **EMA Curta e Longa**: cruzamento de médias móveis
- **RSI (14)**: identifica sobrecompra e sobrevenda
- **MACD e Signal**: tendência e momentum
- **Volume x Média de Volume**: validação de força da movimentação

---

## 🧠 Validação com Inteligência Artificial

A IA utilizada (via Google Generative AI) recebe os dados técnicos filtrados e valida a **confluência e qualidade do sinal** antes de ser enviado. Isso reduz ruído e aumenta a assertividade.

---

## 📦 Requisitos

- Python 3.9+
- Conta no Telegram e bot token
- Conta no Google Cloud para usar o modelo generativo

---

## 🔧 Instalação

```bash
git clone git@github.com:jeffersonbrunoo/bot-futures.git
cd bot-futures
pip install -r requirements.txt
```

Configure o arquivo `.env` com suas credenciais:

```env
TELEGRAM_TOKEN=xxxxxxxxx
TELEGRAM_CHAT_ID=xxxxxxxxx
GOOGLE_API_KEY=xxxxxxxxx
```

---

## 🕒 Agendamento de Execuções

Para rodar a cada 60 minutos:

```bash
python scheduler/main.py
```

Para manter em produção, use ferramentas como:

- **PM2**
- **Cron**
- **Google Cloud Scheduler**

---

## 📲 Exemplo de Sinal no Telegram

```
🚨 SINAL DE VENDA IDENTIFICADO 🚨

Símbolo: BTC_USDT
Entrada: 64.200
Stop Loss: 65.300 ❌
Take Profit: 61.000 ✅

📊 Indicadores Técnicos:
• EMA Curta: 63.800
• EMA Longa: 64.700
• RSI(14): 41.3
• MACD: -0.18 vs Signal: -0.11
• Volume: 450.000 > MA(375.000)

📎 Validado por IA: SIM ✅
```

---

## 💡 Próximos Passos

- Implementar operações automatizadas com API da exchange
- Módulo de backtesting com métricas de desempenho
- Dashboard para acompanhar sinais e resultados

---

## 👨‍💻 Autor

Desenvolvido por Jefferson Bruno(https://www.linkedin.com/in/jbsoousa)  
📩 Contato: bruunosoousaa@gmail.com

---

