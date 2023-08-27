# import the necessary libraries
import openai
import argparse

# set your OpenAI API key
openai.api_key = "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"

def interact_with_chatgpt(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use the ChatGPT-4 engine
        prompt=prompt,
        max_tokens=50  # Adjust as needed
    )
    return response.choices[0].text.strip()

def main():
    parser = argparse.ArgumentParser(description="ChatGPT-4 Command Line Interface")
    parser.add_argument("initial_prompt", type=str, help="Initial prompt for the model")
    args = parser.parse_args()

    initial_prompt = args.initial_prompt
    prompt = f"You: {initial_prompt}\n"

    while True:
        if initial_prompt != "":
            user_input = initial_prompt
            initial_prompt = ""
        else:
            user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Exiting...")
            break
        prompt += f"You: {user_input}\n"
        response = interact_with_chatgpt(prompt)
        print("ChatGPT-4:", response)
#        prompt += f"ChatGPT-5: {response}\n"

if __name__ == "__main__":
    main()