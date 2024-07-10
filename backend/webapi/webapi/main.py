import datetime
import os
import uuid

import requests
import redis
import semantic_kernel as sk
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import KernelArguments, KernelPlugin

from ulid import ULID

from webapi.constants import CHAT_MESSAGE_INDEX_NAME
from webapi.models import AuthorRole, Ask, ChatMessage

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000"
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

greeting = os.getenv("GREETING")
api_key = os.getenv("OPENAI_API_KEY")
redis_uri = os.getenv("REDIS_URI")
kernel_memory_url = os.getenv("KERNEL_MEMORY_URL")

redis_client = redis.from_url(redis_uri)

oai_chat_service = OpenAIChatCompletion(ai_model_id="gpt-3.5-turbo", api_key=api_key)

kernel = sk.Kernel()
kernel.add_service(oai_chat_service)
utility_plugin = KernelPlugin.from_directory("utility", "skills")
kernel.add_plugin(utility_plugin)
utility_functions = utility_plugin.functions

ChatMessage.make_index(redis_client)

def get_memories(question: str) -> str:
    data = {
        "index": "km-py",
        "query": question,
        "limit": 5
    }

    response = requests.post(f"{kernel_memory_url}/search", json=data)

    if response.status_code == 200:
        response_json = response.json()
        memories = response_json.get('results',[])
        res = ""
        for memory in memories:
            res += "memory:"
            for partition in memory['partitions']:
                res += partition['text']
            res += '\n'
        print(res)
        return res

    raise Exception(response.text)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/testenv")
def test_env():
    return {"test_key": os.getenv("TEST_KEY")}


@app.post("/chat/startChat")
def start_chat():
    ulid = ULID()
    msg = ChatMessage(
        pk=uuid.uuid4(),
        message=greeting,
        chatId=str(ulid),
        author_role=AuthorRole.Bot,
        timestamp=int(datetime.datetime.now().timestamp())
    )

    msg.save(redis_client)

    return msg


def formatted_message_history(chat_id: str) -> str:
    query_str = f"@chatId:{{{chat_id}}}"
    messages = redis_client.ft(CHAT_MESSAGE_INDEX_NAME).search(query_str)
    lines = []
    for msg in messages.docs:
        if msg["author_role"] == "AuthorRole.User":
            lines.append(f"User: {msg['message']}")
        else:
            lines.append(f"Bot: {msg['message']}")

    result = '\n'.join(lines)
    return result


async def get_intent(summary: str, ask: Ask) -> str:
    kernel_arguments = KernelArguments(input=ask.prompt, summary=summary)
    intent_function = utility_functions["intent"]
    intent = await kernel.invoke(intent_function, kernel_arguments)
    return str(intent)


async def get_summary(chat_id: str) -> str:
    history = formatted_message_history(chat_id)
    kernel_arguments = KernelArguments(input=history)
    summarize_function = utility_functions["summarize"]
    summary = await kernel.invoke(summarize_function, kernel_arguments)
    return str(summary)


async def get_bot_message(question: str, memories: str, summary: str, chat_id: str) -> ChatMessage:
    kernel_arguments = KernelArguments(input=question, memories=memories, summary=summary)
    chat_function = utility_functions["chat"]
    response = await kernel.invoke(chat_function, kernel_arguments)

    return ChatMessage(
        pk=uuid.uuid4(),
        message=str(response),
        chatId=chat_id,
        author_role=AuthorRole.Bot,
        timestamp=int(datetime.datetime.now().timestamp()))


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    file_content = await file.read()

    data = {
        "index": "km-py",
        "id": str(uuid.uuid4())
    }
    files = {'file': (file.filename, file_content, file.content_type)}

    response = requests.post(f"{kernel_memory_url}/upload", files=files, data=data)
    response.raise_for_status()
    return {"status": response.status_code, "response_data": response.text}


@app.post("/chat/{chat_id}")
async def chat(chat_id: str, ask: Ask):

    user_message = ChatMessage(
        pk = uuid.uuid4(),
        message=ask.prompt.strip(),
        chatId=chat_id,
        author_role=AuthorRole.User,
        timestamp=int(datetime.datetime.now().timestamp())
    )

    summary = await get_summary(chat_id)
    intent = await get_intent(summary, ask)
    memories = get_memories(intent)
    bot_response = await get_bot_message(question=ask.prompt, memories=memories, summary=summary, chat_id=chat_id)

    user_message.save(redis_client)
    bot_response.save(redis_client)

    return bot_response


def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()