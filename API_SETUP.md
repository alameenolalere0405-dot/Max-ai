# MAX AI — API Key Setup Guide
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## What is an API Key?

An API key is a password that lets MAX AI connect to an AI provider's service on your behalf. Each provider requires you to create a free or paid account and generate a key from their dashboard.

Your API keys are stored securely on your computer and are never sent to LEREON Technologies.

---

## Provider Setup

### OpenAI (GPT-4o, o1, o3-mini)
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account.
3. Click **Create new secret key**.
4. Copy the key (starts with `sk-`).
5. Paste into MAX AI Settings → API Keys → OpenAI.

**Cost:** Paid. Add credits at https://platform.openai.com/settings/billing

---

### Anthropic Claude
1. Go to https://console.anthropic.com/settings/keys
2. Sign in or create an account.
3. Click **Create Key**.
4. Copy the key (starts with `sk-ant-`).
5. Paste into MAX AI Settings → Anthropic.

**Cost:** Paid. Free trial credits for new accounts.

---

### Google Gemini
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account.
3. Click **Create API key**.
4. Copy the key (starts with `AIza`).
5. Paste into MAX AI Settings → Gemini.

**Cost:** Free tier available with rate limits.

---

### Groq
1. Go to https://console.groq.com/keys
2. Sign in or create a free account.
3. Click **Create API Key**.
4. Copy the key (starts with `gsk_`).
5. Paste into MAX AI Settings → Groq.

**Cost:** Free tier with generous rate limits. Very fast inference.

---

### DeepSeek
1. Go to https://platform.deepseek.com/api_keys
2. Create an account.
3. Generate an API key.
4. Paste into MAX AI Settings → DeepSeek.

**Cost:** Very low cost per token. Strong coding model.

---

### Mistral AI
1. Go to https://console.mistral.ai/api-keys
2. Create an account.
3. Click **Create new key**.
4. Paste into MAX AI Settings → Mistral.

**Cost:** Free trial, then pay-as-you-go. European provider.

---

### OpenRouter
1. Go to https://openrouter.ai/keys
2. Create a free account.
3. Generate an API key.
4. Paste into MAX AI Settings → OpenRouter.

**Cost:** Varies by model. Gateway to 100+ models from many providers.

---

### Ollama (Local — Free)
1. Download from https://ollama.com/download
2. Install and run: `ollama serve`
3. Pull a model: `ollama pull llama3`
4. In MAX AI Settings → Ollama: enable and set URL to `http://localhost:11434`

**Cost:** Free. Runs entirely on your computer. Requires 4–8 GB RAM depending on model.

---

### Picovoice (Wake Word — "Hey MAX")
1. Go to https://console.picovoice.ai/
2. Create a free account.
3. Copy your Access Key from the dashboard.
4. Add to your `.env` file: `PICOVOICE_ACCESS_KEY=your_key`
5. Enable **Wake Word** in Settings → Voice.

**Cost:** Free tier available.

---

## Adding Keys via .env File

Create or edit `.env` in the MAX AI folder:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=...
PICOVOICE_ACCESS_KEY=...
```

Restart MAX AI after editing this file.

---

## Testing Your Key

After adding a key, MAX AI tests it automatically in the Setup Wizard. You can re-test at any time by clicking **Verify** in the Settings dialog.

If the test fails:
- Check you copied the full key with no spaces.
- Check your account has billing set up (for paid providers).
- Check your internet connection.
- Check the provider's status page for outages.
