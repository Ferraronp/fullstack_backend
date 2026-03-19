import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT = 15.0
MAX_RETRIES = 2


def _build_prompt(operations: list[dict]) -> str:
    if not operations:
        return "Операций нет."
    lines = []
    for op in operations:
        cat = op.get("category", {})
        cat_name = cat.get("name", "Без категории") if cat else "Без категории"
        sign = "+" if op["amount"] >= 0 else ""
        lines.append(f"- {op['date']}: {sign}{op['amount']} ₽, категория: {cat_name}, комментарий: {op.get('comment') or '—'}")
    return "\n".join(lines)


async def analyze_operations(operations: list[dict]) -> str:
    """Отправляет операции в Groq и возвращает текстовый анализ."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY не задан")

    prompt = _build_prompt(operations)
    messages = [
        {
            "role": "system",
            "content": (
                "Ты финансовый аналитик. Пользователь предоставил список своих финансовых операций. "
                "Проанализируй их кратко: на что больше всего тратится, есть ли тревожные паттерны, "
                "дай 2-3 конкретных совета по оптимизации расходов. "
                "Отвечай на русском языке, кратко и по делу, без лишней воды. Максимум 200 слов."
            ),
        },
        {
            "role": "user",
            "content": f"Вот мои операции за последнее время:\n{prompt}\n\nПроанализируй.",
        },
    ]

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": messages,
                        "max_tokens": 400,
                        "temperature": 0.7,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException as e:
            last_error = f"Таймаут запроса к Groq (попытка {attempt + 1})"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                last_error = "Превышен лимит запросов к Groq API"
                break  # не ретраим при rate limit
            last_error = f"Ошибка Groq API: {e.response.status_code}"
        except Exception as e:
            last_error = f"Ошибка при обращении к Groq: {str(e)}"

    raise RuntimeError(last_error or "Неизвестная ошибка Groq")
