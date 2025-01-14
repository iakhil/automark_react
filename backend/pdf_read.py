from openai import OpenAI
from openai.types.beta.threads.message_create_params import (
    Attachment,
    AttachmentToolFileSearch,
)
import os
from dotenv import load_dotenv




filename = "answer.pdf"
prompt = "Extract the content from the file provided without altering it. What does the first line say?"
load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

file_url = 'https://res.cloudinary.com/dewujwyee/image/upload/v1736838480/Screenshot_2025-01-14_at_1.07.50_AM_wqig5q.png'
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What does the image say?"},
                {"type": "image_url", "image_url": {"url": file_url}},
            ],
        }
    ],
    max_tokens=300,
)

# Extract the response
ai_response = response.choices[0].message.content

print(ai_response)


# pdf_assistant = client.beta.assistants.create(
#     model="gpt-4o",
#     description="An assistant to extract the contents of PDF files.",
#     tools=[{"type": "file_search"}],
#     name="PDF assistant",
# )

# # Create thread
# thread = client.beta.threads.create()

# file = client.files.create(file=open(filename, "rb"), purpose="assistants")

# # Create assistant
# client.beta.threads.messages.create(
#     thread_id=thread.id,
#     role="user",
#     attachments=[
#         Attachment(
#             file_id=file.id, tools=[AttachmentToolFileSearch(type="file_search")]
#         )
#     ],
#     content=prompt,
# )

# # Run thread
# run = client.beta.threads.runs.create_and_poll(
#     thread_id=thread.id, assistant_id=pdf_assistant.id, timeout=1000
# )

# if run.status != "completed":
#     raise Exception("Run failed:", run.status)

# messages_cursor = client.beta.threads.messages.list(thread_id=thread.id)
# messages = [message for message in messages_cursor]

# # Output text
# res_txt = messages[0].content[0].text.value
# print(res_txt)