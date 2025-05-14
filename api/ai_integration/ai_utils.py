from .models import TokenUsageLog
import logging

def chat_with_ai(client, model, messages, source="unknown", **kwargs):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        usage = response.usage
        if usage:
            TokenUsageLog.objects.create(
                model_name=model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                source=source
            )
        return response

    except Exception as e:
        logging.error(f"AI request failed: {e}")
        return None
