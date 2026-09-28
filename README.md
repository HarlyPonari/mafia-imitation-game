# Mafia Imitation Game
A project meant to test Alan Turing's Paper 'The Imitation Game' with modern Artificial Intelligence like Generative AI. Built using python, and the discord API to create a both that tests the question "Can Machines Think".



## Setup
1. Ensure python (3.11+) is installed on the machine
2. Create the python virtual environemnt via the command `python -m venv .venv` or `python3` depends on your install
3. Create a `.env` file inside of the repo and fill in these variables with your credentials
    - `DISCORD_TOKEN: str`   the discord bot token
    - `OPENROUTER_API_KEY: str` the api key for openrouter (may be changed in the future)
    - `GUILD_ID: str | None` optional
4. Enable the virtual environment depends on your OS:
    - Windows: inside of a powershell terminal and run (while within the project directry) `.venv\Scripts\activate`
    - Linux: inside of a shell run (while within the project directory) `source .venv\bin\activate` 
5. Install the requirements for the bot `pip install -r requirements.txt`
6. Run the main file `python3 main.py`
