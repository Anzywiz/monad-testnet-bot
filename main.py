from utils import run_all, data, verify_github_star
import asyncio

repo_to_check = "https://github.com/Anzywiz/monad-testnet-bot"

# Only proceed if repository is starred
if verify_github_star(repo_to_check):
    # Your script logic goes here
    print("Proceeding with script...")
else:
    raise Exception(f"Access denied. Please star the repository {repo_to_check} first.")


private_keys = data["PRIVATE_KEYS"]
asyncio.run(run_all(private_keys))
