import aiohttp
import asyncio
import random
import json
import sys
from colorama import *
from fake_useragent import UserAgent
from utils.utils import _banner, get_random_color, read_config, reset
from utils.agent import generate_random_user_agent

init(autoreset=True)
ua = UserAgent()
config = read_config()
class DuckChainAPI:
    def __init__(self, authorization, proxy=None, timeout=10):
        self.base_url = "https://preapi.duckchain.io"
        self.authorization = f'tma {authorization}'
        self.headers = {
            "accept": "*/*",
            "if-none-match": 'W/"129-83t1ejiXqZksI6D5DMDXM+paHE4"',
            "authorization": self.authorization,
            "origin": "https://preapi.duckchain.io",
            "priority": "u=1, i",
            "referer": "https://preapi.duckchain.io/",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Android WebView\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": generate_random_user_agent()
        }
        self.proxy = proxy
        self.timeout = timeout

    async def _make_request(self, session, endpoint):
        url = f"{self.base_url}{endpoint}"
        try:
            async with session.get(url, headers=self.headers, proxy=self.proxy, timeout=self.timeout) as response:
                response.raise_for_status()
                try:
                    json_response = await response.json()
                    return json_response
                except aiohttp.ContentTypeError:
                    return None
        except asyncio.TimeoutError:
            return None
        except aiohttp.ClientError as e:
            return None

    async def get_user_info(self, session):
        return await self._make_request(session, "/user/info")

    async def execute_tap(self, session):
        return await self._make_request(session, "/quack/execute")

def get_random_proxy():
    try:
        with open('proxies.txt', 'r') as file:
            proxies = [line.strip() for line in file if line.strip()]
        return f"http://{random.choice(proxies)}"
    except FileNotFoundError:
        print("File 'proxies.txt' not found.")
        return None

async def main():
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print("File 'config.json' not found.")
        return

    use_proxy = config.get("use_proxy", False)
    quack_delay = config.get("quack_delay", 0)

    try:
        with open('tokens.txt', 'r') as file:
            tokens = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("File 'tokens.txt' not found.")
        return

    if not tokens:
        print("No tokens found in tokens.txt")
        return

    apis = [DuckChainAPI(token, get_random_proxy() if use_proxy else None) for token in tokens]

    async with aiohttp.ClientSession() as session:
        while True:
            user_info_tasks = [api.get_user_info(session) for api in apis]
            execute_tap_tasks = [api.execute_tap(session) for api in apis]

            user_info_results = await asyncio.gather(*user_info_tasks)
            execute_tap_results = await asyncio.gather(*execute_tap_tasks)

            output = ""
            for i in range(len(apis)):
                user_info = user_info_results[i]
                execute_tap = execute_tap_results[i]

                if user_info and isinstance(user_info, dict) and 'data' in user_info:
                    decibels = int(user_info['data'].get('decibels', 0))
                    if decibels < 1:
                        output += (f"{Fore.RED}Account stopped: {Fore.WHITE}{user_info['data'].get('duckName', 'N/A')} {Fore.RED}has 0 decibels.\n{reset}")
                        continue
                else:
                    output += f"{Fore.RED}Error fetching user info for account {i + 1}.\n{reset}"
                    continue

                if execute_tap and isinstance(execute_tap, dict) and 'data' in execute_tap:
                    quack_records = execute_tap['data'].get('quackRecords', [])
                    A = quack_records[8] if len(quack_records) > 8 else None
                    B = quack_records[0] if len(quack_records) > 0 else None
                    result = A if A else B if B else "??"

                    decibel_value = execute_tap['data'].get('decibel', 'N/A')
                else:
                    result = "??"
                    decibel_value = "N/A"

                color = get_random_color()
                output += (f"{color}{user_info['data'].get('duckName', 'N/A')}, {reset}"
                        f"Box: {color}{user_info['data'].get('boxAmount', 'N/A')}, {reset}"
                        f"Quack: {color}{decibel_value}, {reset}"
                        f"Record: {color}{result}, {reset}"
                        f"Quack Time: {color}{user_info['data'].get('quackTimes', 'N/A')}\n{reset}")

            print("\033c", end="")
            print(output, end="")
            await asyncio.sleep(quack_delay)

if __name__ == "__main__":
    while True:
        _banner()
        print(Fore.LIGHTGREEN_EX + f" Please wait starting your bot...")
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print()
            print(Fore.LIGHTRED_EX + f"Successfully logged out of the bot\n")
            sys.exit()