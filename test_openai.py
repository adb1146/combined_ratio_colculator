import openai
import os

# Set API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Main code for generating a completion
try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "What is the best ratio?"}
        ]
    )
    # Display the response
    print(response['choices'][0]['message']['content'])
except Exception as e:
    print(f"An error occurred with the OpenAI API: {e}")