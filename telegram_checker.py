import asyncio
import random
import string
import time

from colorama import Fore, init
from telethon import TelegramClient, functions, types

init(autoreset=True)

class TelegramChecker:
    def __init__(self):
        self.checked = 0
        self.available = 0
        self.unavailable = 0
        self.run = True
        self.target_available = 1005   
        self.api_id = None
        self.api_hash = None
        
        print(f"{Fore.CYAN}===== Telegram Username Checker (API Version) =====")
        
        print(f"{Fore.YELLOW}You need to provide your Telegram API credentials.")
        print(f"{Fore.YELLOW}If you don't have them, get them from https://my.telegram.org/apps")
        self.api_id = input("Enter your API ID: ").strip()
        self.api_hash = input("Enter your API Hash: ").strip()
        self.phone = input("Enter your phone number (with country code, e.g. +12345678901): ").strip()
        
        self.mode = input(f"Choose mode:\n1. Check from file\n2. Check random usernames\n3. Check specific username\nEnter choice (1-3): ").strip()
        
        if self.mode == "1":
            self.file_path = input("Enter file path containing usernames: ").strip()
            self.usernames = self.load_usernames()
        elif self.mode == "2":
            self.length = int(input("Enter username length: ").strip())
            self.count = int(input("Enter number of usernames to check (or press Enter for unlimited until 1005 available): ").strip() or 0)
        elif self.mode == "3":
            self.username = input("Enter username to check: ").strip()
        else:
            print(f"{Fore.RED}Invalid choice. Exiting.")
            exit()
            
        self.start()
    
    def load_usernames(self):
        try:
            with open(self.file_path, 'r') as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"{Fore.RED}File not found. Exiting.")
            exit()
    
    def generate_random_username(self):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(self.length))
    
    async def check_username_api(self, client, username):
        try:
            try:
                result = await client(functions.contacts.ResolveUsernameRequest(username=username))
                self.unavailable += 1
                print(f"{Fore.RED}[TAKEN] {username}")
            except Exception as resolve_error:
                error_message = str(resolve_error).lower()
                print
                if "the username is not in use by anyone else yet" in error_message:
                    self.available += 1
                    print(f"{Fore.GREEN}[AVAILABLE] https://t.me/{username}")
                    with open("available_telegram.txt", "a") as file:
                        file.write(f"https://t.me/{username}\n")
                else:
                    return
                    
            self.checked += 1
                
        except Exception as e:
            print(f"{Fore.YELLOW}[ERROR] {username}: {str(e)}")
    
    def print_status(self):
        print(f"\r{Fore.CYAN}Checked: {self.checked} | {Fore.GREEN}Available: {self.available} | {Fore.RED}Unavailable: {self.unavailable}", end='', flush=True)
    
    async def process_usernames(self, client, usernames):
        for username in usernames:
            if not self.run or self.available >= self.target_available:
                break
            await self.check_username_api(client, username)
            self.print_status()
            await asyncio.sleep(2)
    
    async def process_random_usernames(self, client, count=None):
        checked = 0
        while (count is None or checked < count) and self.run and self.available < self.target_available:
            username = self.generate_random_username()
            await self.check_username_api(client, username)
            checked += 1
            self.print_status()
            await asyncio.sleep(2)
    
    async def run_client(self, worker_func, *args):
        session_name = 'anon_session'
        client = TelegramClient(session_name, self.api_id, self.api_hash)
        
        await client.start(phone=self.phone)
        
        if not await client.is_user_authorized():
            print(f"\n{Fore.YELLOW}You need to login to your Telegram account.")
            print(f"{Fore.YELLOW}Please check your phone for the verification code.")
            await client.start(phone=self.phone)
            
        try:
            await worker_func(client, *args)
        finally:
            await client.disconnect()
    
    def start(self):
        print(f"{Fore.CYAN}Starting username checker...")
        
        try:
            loop = asyncio.get_event_loop()
            
            if self.mode == "1":
                loop.run_until_complete(self.run_client(self.process_usernames, self.usernames))
                print(f"\n{Fore.YELLOW}All usernames checked from file.")
                
            elif self.mode == "2":
                loop.run_until_complete(self.run_client(self.process_random_usernames, self.count))
                if self.count > 0:
                    print(f"\n{Fore.YELLOW}Completed checking {self.count} random usernames.")
                else:
                    print(f"\n{Fore.GREEN}Target of {self.target_available} available usernames reached!")
                    
            elif self.mode == "3":
                async def single_check_worker(client):
                    await self.check_username_api(client, self.username)
                    
                loop.run_until_complete(self.run_client(single_check_worker))
                print("\nUsername check completed.")
                
        except KeyboardInterrupt:
            self.run = False
            print(f"\n{Fore.YELLOW}Interrupted by user. Stopping...")
        
        print(f"\n{Fore.CYAN}Final Results:")
        print(f"{Fore.CYAN}Checked: {self.checked} | {Fore.GREEN}Available: {self.available} | {Fore.RED}Unavailable: {self.unavailable}")
        
        if self.available > 0:
            print(f"{Fore.GREEN}Available usernames saved as https://t.me/username links in available_telegram.txt")

if __name__ == "__main__":
    TelegramChecker()