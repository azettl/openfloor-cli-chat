#!/usr/bin/env python3

import argparse
import sys
from openfloor_client import OpenFloorClient


class OpenFloorCLI:
    """Command-line interface for Open Floor agents"""
    
    def __init__(self):
        self.client = OpenFloorClient()
        self.current_agent_url = None
    
    def print_banner(self):
        """Print a welcoming banner"""
        print("=" * 60)
        print("🤖 Open Floor Protocol CLI Client")
        print("=" * 60)
        print("Commands:")
        print("  manifest <agent_url>  - Get agent capabilities")
        print("  chat <agent_url>      - Start a chat session")
        print("  help                  - Show this help")
        print("  quit                  - Exit the CLI")
        print("=" * 60)


    def cmd_manifest(self, agent_url: str):
        """Fetch and display agent manifest"""
        manifests = self.client.get_manifest(agent_url)
        if manifests is None:
            print("❌ Failed to fetch manifest")
            return
        
        formatted_manifest = self.client.format_manifest(manifests)
        print(formatted_manifest)
        
        # Store the URL for potential chat later
        self.current_agent_url = agent_url


    def cmd_chat(self, agent_url: str):
        """Start an interactive chat session"""
        print(f"🗣️ Starting chat with: {agent_url}")
        print("Type 'exit' to end the chat session\n")
        
        self.current_agent_url = agent_url
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Chat session ended")
                    break
                
                if not user_input:
                    continue
                
                response = self.client.send_message(agent_url, user_input)
                if response:
                    print(f"Agent: {response}")
                else:
                    print("❌ Failed to get response from agent")
                
            except KeyboardInterrupt:
                print("\n👋 Chat session ended")
                break
            except EOFError:
                print("\n👋 Chat session ended")
                break


    def run_interactive(self):
        """Run the interactive CLI"""
        self.print_banner()
        
        while True:
            try:
                command_line = input("\n> ").strip()
                
                if not command_line:
                    continue
                
                parts = command_line.split(None, 1)
                command = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                if command in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif command == 'help':
                    self.print_banner()
                elif command == 'manifest':
                    if not arg:
                        if self.current_agent_url:
                            print(f"Using last agent: {self.current_agent_url}")
                            arg = self.current_agent_url
                        else:
                            print("❌ Please provide an agent URL")
                            continue
                    self.cmd_manifest(arg)
                elif command == 'chat':
                    if not arg:
                        if self.current_agent_url:
                            print(f"Using last agent: {self.current_agent_url}")
                            arg = self.current_agent_url
                        else:
                            print("❌ Please provide an agent URL")
                            continue
                    self.cmd_chat(arg)
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break


    def run_single_command(self, args):
        """Run a single command from command line arguments"""
        if args.command == 'manifest':
            self.cmd_manifest(args.url)
        elif args.command == 'chat':
            self.cmd_chat(args.url)
        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='OpenFloor Protocol CLI Client')
    parser.add_argument('command', nargs='?', choices=['manifest', 'chat'], 
                       help='Command to run (manifest or chat)')
    parser.add_argument('url', nargs='?', help='Agent URL')
    
    args = parser.parse_args()
    
    cli = OpenFloorCLI()
    
    if args.command:
        if not args.url:
            print("❌ Agent URL is required for this command")
            sys.exit(1)
        cli.run_single_command(args)
    else:
        cli.run_interactive()

if __name__ == "__main__":
    main()