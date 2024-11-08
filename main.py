from dotenv import load_dotenv
import openai
import time
import os
import sys
import json
import random
from colorama import Fore, Style

load_dotenv()

# Function to retrieve the OpenAI API key from environment variables
def get_api_key():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print(Fore.RED + "Error: The OpenAI API key is not set." + Style.RESET_ALL)
        print(Fore.YELLOW + "Please set the OPENAI_API_KEY environment variable and try again." + Style.RESET_ALL)
        sys.exit(1)
    return api_key

# Function to get user input for the research idea
def get_research_idea():
    print(Fore.CYAN + "Welcome to the Idea Attorney!" + Style.RESET_ALL)
    print(Fore.GREEN + "Please enter your research idea below. When you're done, press Enter.\n" + Style.RESET_ALL)
    research_idea = ""
    print(Fore.BLUE + "Enter your research idea (press Enter twice to finish):" + Style.RESET_ALL)
    while True:
        line = input()
        if line == "":
            break
        research_idea += line + "\n"
    if not research_idea.strip():
        print(Fore.RED + "Error: No research idea provided. Exiting." + Style.RESET_ALL)
        sys.exit(1)
    return research_idea.strip()

# Function to interact with the OpenAI API
def get_response(client, messages, temperature=0.7, max_tokens=5000):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        print(Fore.RED + f"OpenAI API Error: {e}" + Style.RESET_ALL)
        sys.exit(1)

# Function to save the conversation to a JSON file with a random filename
def save_conversation_to_json(research_idea, debate_topic, defender_responses, critic_responses, judge_decisions, summary_response):
    conversation_data = {
        "research_idea": research_idea,
        "debate_topic": debate_topic,
        "iterations": []
    }

    for i in range(len(defender_responses)):
        iteration_data = {
            "iteration": i + 1,
            "defender_response": defender_responses[i],
            "critic_response": critic_responses[i],
            "judge_decision": judge_decisions[i]
        }
        conversation_data["iterations"].append(iteration_data)

    conversation_data["summary_of_pros_and_cons"] = summary_response

    filename = time.strftime("debate_summary_%Y%m%d_%H%M%S.json")
    with open(filename, "w") as json_file:
        json.dump(conversation_data, json_file, indent=4)

    print(Fore.MAGENTA + f"Conversation saved to {filename}" + Style.RESET_ALL)

def main():
    # Retrieve the API key
    openai.api_key = get_api_key()

    # Initialize clients for Defender, Critic, and Judge
    defender_client = openai.OpenAI()
    critic_client = openai.OpenAI()
    judge_client = openai.OpenAI()
    summary_client = openai.OpenAI()

    # Get the research idea from the user
    research_idea = get_research_idea()

    # Initialize the different conversation histories
    defender_history = [
        {"role": "system", "content": "You are an expert in research proposal analysis. You are the Defender. Your task is to present strong arguments supporting the research idea, refine existing points, and propose new ones to strengthen the research proposal."},
    ]

    critic_history = [
        {"role": "system", "content": "You are an expert in research proposal analysis. You are the Critic. Your task is to argue against the research idea as sharply as possible, highlighting every possible weakness, flaw, and logical loophole as sharp and impolite as possible."},
    ]

    judge_history = [
        {"role": "system", "content": "You are an expert in research proposal analysis. You are the Judge. Your task is to Look at the defender's and critic's responses and decide whether the debate should go on or the debate got stuck or there is already a winner. Simply respond with 'Defender wins', 'Critic wins', 'Stuck' or 'Continue'"},
    ]

    # Judge starts the debate by setting a debate topic
    judge_topic_prompt = [
        {"role": "system", "content": "You are an expert in research proposal analysis. You are the Judge. Your task is to start the debate by providing a specific debate topic or aspect of the research idea that the Defender and Critic should focus on."},
        {"role": "user", "content": research_idea}
    ]
    debate_topic = get_response(judge_client, judge_topic_prompt, max_tokens=150)
    print(Fore.YELLOW + "Judge's Debate Topic:" + Style.RESET_ALL)
    print(debate_topic + "\n")

    # Add the debate topic to the Defender and Critic histories
    defender_history.append({"role": "user", "content": f"Judge's Debate Topic: {debate_topic}"})
    critic_history.append({"role": "user", "content": f"Judge's Debate Topic: {debate_topic}"})
    judge_history.append({"role": "user", "content": f"Judge's Debate Topic: {debate_topic}"})

    iteration = 1
    max_iterations = 10  # Prevent infinite loops

    print("\n--- Starting the Refinement Process ---\n")

    all_defender_responses = []
    all_critic_responses = []
    all_judge_decisions = []

    while iteration <= max_iterations:

        print(f"\n--- Iteration {iteration} ---\n")

        # Defender's turn
        defender_response = get_response(defender_client, defender_history)
        defender_history.append({"role": "assistant", "content": defender_response})
        critic_history.append({"role": "user", "content": defender_response})  # Critic should see the Defender's response
        judge_history.append({"role": "user", "content": f"Defender's Response: {defender_response}"})
        all_defender_responses.append(defender_response)
        
        print(Fore.GREEN + "Defender's Response:" + Style.RESET_ALL)
        print(defender_response)
        print("\n")

        # Critic's turn
        critic_response = get_response(critic_client, critic_history)
        critic_history.append({"role": "assistant", "content": critic_response})
        defender_history.append({"role": "user", "content": critic_response})  # Defender should see the Critic's response
        judge_history.append({"role": "user", "content": f"Critic's Response: {critic_response}"})
        all_critic_responses.append(critic_response)
        
        print(Fore.RED + "Critic's Response:" + Style.RESET_ALL)
        print(critic_response)
        print("\n")

        # Judge's turn
        judge_decision = get_response(judge_client, judge_history, max_tokens=150)
        judge_history.append({"role": "assistant", "content": judge_decision})
        all_judge_decisions.append(judge_decision)
        
        print(Fore.YELLOW + "Judge's Decision:" + Style.RESET_ALL)
        print(judge_decision)
        print("\n")

        # Process Judge's decision
        if 'defender wins' in judge_decision.lower():
            print(Fore.GREEN + "✅ The research idea has been accepted as robust and well-defended." + Style.RESET_ALL)
            break
        elif "critic wins" in judge_decision.lower():
            print(Fore.RED + "❌ The research idea has been rejected due to significant flaws." + Style.RESET_ALL)
            break
        elif 'continue' in judge_decision.lower():
            print(Fore.YELLOW + "🔄 Further refinement is needed to strengthen the research idea." + Style.RESET_ALL)
            iteration += 1
            time.sleep(1)  # To avoid hitting API rate limits
        elif 'stuck' in judge_decision.lower():
            print(Fore.YELLOW + "🔒 The debate is stuck. Further intervention may be needed." + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "⚠️ Judge's decision was unclear. Stopping the process." + Style.RESET_ALL)
            break
    else:
        print(Fore.RED + "⚠️ Maximum iterations reached without a conclusive decision." + Style.RESET_ALL)

    # Summarize pros and cons based on the entire debate
    all_defender_arguments = "\n".join(all_defender_responses)
    all_critic_arguments = "\n".join(all_critic_responses)
    summary_prompt = [
        {"role": "system", "content": "You are an expert in summarizing debates. Your task is to provide a summary of the pros and cons of the research idea based on the arguments presented by the Defender and Critic throughout the entire debate."},
        {"role": "user", "content": f"Defender's Arguments: {all_defender_arguments}\nCritic's Arguments: {all_critic_arguments}"}
    ]
    summary_response = get_response(summary_client, summary_prompt, max_tokens=5000)
    print(Fore.CYAN + "Summary of Pros and Cons:" + Style.RESET_ALL)
    print(summary_response)
    print("\n")

    # Save the entire conversation to a JSON file with a random filename
    save_conversation_to_json(research_idea, debate_topic, all_defender_responses, all_critic_responses, all_judge_decisions, summary_response)

    print("\n--- Refinement Process Completed ---\n")

if __name__ == "__main__":
    main()
    # My research idea is to build a large language model with a hidden-space memory. However, people were arguing that it requires retraining, while agents with memory where the memory is token-level does not require retraining and can be easily up-to-date whenever openai has new models coming out. To argue that a hidden-space memory is necessary, I think: Agent with memory may (1) lacks sophisticated mechanisms to integrate and contextualize this knowledge deeply; (2) Generally lacks mechanisms to process emotions. (3) Often lacks mechanisms for long-term adaptation based on accumulated experiences.
    # I want to build a benchmark with long book question answering. However, instead of constructing simple questions related to some plot in the book, I aim to create a event list for a long book, and then ask the target model to generate the event given the existing event. If the target model can generate the event then it means this model still remembers the information in the book.