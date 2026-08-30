import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def generate_justification(jd_text: str, resume_text: str) -> str:
    prompt = f"""You are screening a candidate for a job. Given the job description and resume below,
write a 2-sentence justification for how well this candidate matches, mentioning specific overlapping skills or experience.

Job Description:
{jd_text[:1500]}

Resume:
{resume_text[:1500]}
"""

    # fallback-method
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",  # confirm exact string from Groq's model list
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM justification failed: {e}")
        return 