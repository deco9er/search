# DECO9ER Search

терминальный поисковый ассистент с DuckDuckGo и Mistral API.

## Возможности

- поиск через DuckDuckGo
- краткая AI-сводка через Mistral
- hacker-style terminal UI
- stdlib only
- команды `/help`, `/clear`, `/key`, `/exit`

## Установка

```bash
pip install colorama
```

## Запуск

```bash
python dec.py
```

## API Key

Linux/macOS:

```bash
export MISTRAL_API_KEY="your_api_key"
```

Windows:

```powershell
setx MISTRAL_API_KEY "your_api_key"
```

## Стек

- Python
- DuckDuckGo
- Mistral API
- Colorama
