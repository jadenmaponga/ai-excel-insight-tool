import pandas as pd
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Excel dataset
df = pd.read_excel("data.xlsx")

# Preview dataset
preview = df.head().to_string()

prompt = f"""
You are a data analyst.

Analyze the dataset below and give key insights:

{preview}
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print(response.choices[0].message.content)