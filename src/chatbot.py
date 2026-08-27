import os
from groq import Groq


def create_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    return Groq(
        api_key=api_key
    )


def ask_chatbot(question, context):

    client = create_client()

    if client is None:
        return (
            "Groq API key not found. "
            "Please set GROQ_API_KEY in your environment."
        )

    system_prompt = """
You are GridLens, an electricity-market analytics assistant.

You answer questions about the German electricity market
using ONLY the statistics supplied by the application.

Rules:

1. Use the supplied data.
2. Never invent numerical values.
3. If the supplied data does not answer the question,
   clearly say that.
4. Correlation does not mean causation.
5. Explain energy concepts in simple language.
6. Mention the relevant numbers when useful.
7. Give a direct answer first.
8. Keep the response concise and professional.
"""

    user_prompt = f"""
Here is the analytical context calculated from the
GridLens SMARD dataset:

{context}

User question:

{question}

Answer using the available analytical context.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2,
        max_completion_tokens=700
    )

    return response.choices[0].message.content