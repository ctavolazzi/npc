
# Setup environment
import textworld
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain import OpenAI, LLMChain

from dotenv import load_dotenv
load_dotenv()

# Setup the language model
llm = OpenAI(
    model_name="text-davinci-003",
    temperature=0.0,
    max_tokens=100,
    # stop=["\n","\r"],
)

# Setup the environment
infos = textworld.EnvInfos(
    feedback=True,    # Response from the game after typing a text command.
    description=True, # Text describing the room the player is currently in.
    inventory=True,    # Text describing the player's inventory.
    max_score=True,   # Maximum score obtainable in the game.
    score=True,       # Score obtained so far.
)
env = textworld.start('./zork1.z5', infos=infos)
game_state = env.reset()

# Tool for sending commmands to the game environment and getting back templated world state
def send_command(command):
    """Send a command to the game and receive feedback."""
    game_state, score, done = env.step(command)
    description = "" #if game_state.description == game_state.feedback else f"{game_state.description}"
    templated_feedback = f"""{description}{game_state.feedback}
(Score: {game_state.score}/{game_state.max_score}, Moves: {game_state.moves}, DONE: {done})
"""
    return templated_feedback

tools = [Tool("Play", send_command, send_command.__doc__)]


# Setup the agent with prompt and tools and memory
prefix = """You are playing a text adventure game. Explore the world and discover its secrets!
You have access to the following tools:"""
suffix = """
{chat_history}
{input}
{agent_scratchpad}"""

prompt = ZeroShotAgent.create_prompt(
    tools, 
    prefix=prefix, 
    suffix=suffix, 
    input_variables=[
        "input", 
        "chat_history", 
        "agent_scratchpad"]
)

memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=0,
    )

llm_chain = LLMChain(llm=llm, prompt=prompt,
 verbose=True
 )
agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools, 
    memory=memory,
    verbose=True,
    max_iterations=20,
)

# Play the game
def play_game(env, agent_executor):
    game_state = env.reset()
    prefix = f"""{game_state.description}"""

    print(prefix)
    agent_executor.run(prefix)
    print("Played {} steps, scoring {} points.".format(game_state.moves, game_state.score))

    
# Play the game
if __name__ == "__main__":   
    # argparse for how many steps to play
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--save", type=bool, default=False)
    args = parser.parse_args()

    agent_executor.max_iterations = args.steps

    # If we're saving the log, we have to divert the output to a file
    if args.save:
        import sys
        import os
        sys.stdout = open(os.path.join(os.getcwd(), "log.md"), "w")
        play_game(env, agent_executor)
        sys.stdout.close()
    else:
        play_game(env, agent_executor)