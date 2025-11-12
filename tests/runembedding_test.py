module load os
import os, litellm
litellm.return_response_headers = True
litellm.api_base = "https://mindweaver.develop.ivcap.io/litellm/"
from litellm import embedding
help(embedding)
litellm.api_key = os.getenv("$IVCAP_TOKEN")
print(litellm.api_key)
print(os.getenv("$IVCAP_TOKEN"))
print(os.environ.get("$IVCAP_TOKEN"))
!echo $IVCAP_TOKEN
print(os.environ.get("IVCAP_TOKEN"))
litellm.api_key = os.environ.get("$IVCAP_TOKEN")
embedding_response = litellm.embedding(
    model="text-embedding-ada-002",
    input="hello",
)

embedding_response_headers = embedding_response._response_headers
print("embedding_response_headers=", embedding_response_headers)
help(litellm.embedding)
embedding_response = litellm.embedding(
    model="text-embedding-3-small",
    input="hello",
)

embedding_response_headers = embedding_response._response_headers
print("embedding_response_headers=", embedding_response_headers)
%history
litellm.embedding(
    model="text-embedding-ada-002",
    input="hello",
)
esponse = completion(
    model="gpt-5",
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
from litellm import completion
esponse = completion(
    model="gpt-5",
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
%history
esponse = completion(
    model="gpt-5",
    api_key = os.getenv("LITELLM_API_KEY"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm/",
   
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
esponse = completion(
    model="gpt-5",
    api_key = os.getenv("LITELLM_API_KEY"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm/v1/chat/completions",
   
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
response = completion(
    model="gpt-5",
    api_key = os.getenv("LITELLM_API_KEY"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm/v1/chat/completions",
   
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
response = completion(
    model="gpt-5",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm/v1/chat/completions",
   
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
response = completion(
    model="gpt-5",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm/v1",
   
    messages=[
        {
            "role": "user",
            "content": "hi",
        }
    ],
)
print(f"response: {response}")
print("_response_headers=", response._response_headers)
help(embedding)
print(help(embedding))
embedding_response = litellm.embedding(
    model="text-embedding-ada-002",
    input="hello",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm"
)
embedding_response_headers = embedding_response._response_headers
print("embedding_response_headers=", embedding_response_headers)
import pprint
embedding_response_headers = embedding_response._response_headers
pprint("embedding_response_headers=", embedding_response_headers)
pprint.pprint("embedding_response_headers=", embedding_response_headers)
embedding_response = litellm.embedding(
    model="text-embedding-ada-002",
    input="hello",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm"
)
embedding_response = litellm.embedding(
    model="gemini-embedding-001",
    input="hello",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm"
)
%history
embedding_response = litellm.embedding(
    model="gemini-embedding-001",
    input="hello",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm"
)
embedding_response = litellm.embedding(
    model="text-embedding-ada-002",
    input="hello",
    api_key = os.getenv("IVCAP_TOKEN"),
    api_base = "https://mindweaver.develop.ivcap.io/litellm"
)
%history > runembedding_test.py
!ls
%history -h
%history -f runembedding_test.py
