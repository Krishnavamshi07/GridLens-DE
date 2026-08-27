import os
from groq import Groq


def generate_briefing(summary):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Groq API key not found."

    client = Groq(
        api_key=api_key
    )

    prompt = f"""
You are an energy-market analyst.

Write a short and professional briefing about the
German electricity market using ONLY the statistics
provided below.

Do not invent facts.

Focus on:
1. Renewable vs fossil generation
2. Seasonal differences
3. Electricity prices
4. Negative-price hours
5. Renewable price effectiveness
6. Peak-demand conditions

Keep it easy to read for a business user.

Statistics:

{summary}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful German electricity "
                    "market analyst."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_completion_tokens=500
    )

    return response.choices[0].message.content