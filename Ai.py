import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:4b"

messages = [
    {"role": "system", "content": "You are ALLICE, a helpful coding assistant."}
]

def chat_with_ollama():
    print("ALLICE Terminal Chat Started (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit" or user_input.lower() == "quit" or user_input.lower() == "bye":
         break

        messages.append({"role": "user", "content": user_input})

        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload)
        data = response.json()
        print(data)
        reply = data["message"]["content"]

        print("ALLICE:", reply, "\n")

        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    chat_with_ollama()