
# Building a CLI Client with the Python SDK

In this guide, we'll build a command-line client for interacting with Open Floor Protocol agents using Python. The CLI client will let you discover agent capabilities and have conversations with any Open Floor Protocol-compliant agent, perfect for quick testing and automation.

**TL;DR:** We'll create a CLI tool that can fetch agent manifests and chat with agents like the parrot agent from our previous tutorial.

## What We're Building

Our CLI client will have these main features:

-   **Interactive Mode**: A command prompt where you can run multiple commands
-   **Manifest Discovery**: Fetch and display an agent's capabilities
-   **Chat Interface**: Have real-time conversations with agents
-   **Direct Commands**: Run single commands from the terminal

## Initial Setup

First, let's set up our project by creating the project folder and installing the required packages:

```bash
mkdir openfloor-cli-client
cd openfloor-cli-client
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Create a `requirements.txt` file with the following content:

```txt
--extra-index-url https://test.pypi.org/simple/
events==0.5
jsonpath-ng>=1.5.0
openfloor
requests
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

Now that the basic setup is done, let's start coding together!

## Step 1: Building the Core Client Logic

Let's create our main client file. Create a new file `openfloor_client.py`, this will contain the core Open Floor communication logic.

### Step 1.1: Add the imports

Let's start with importing everything we need from the [openfloor package](https://test.pypi.org/project/openfloor/):

```python
from openfloor import (
    Envelope,
    Payload,
    GetManifestsEvent,
    UtteranceEvent,
    DialogEvent,
    TextFeature,
    To,
    Sender,
    Conversation
)
import requests
import json
import uuid
from typing import Optional, List, Dict, Any
```

**Why these imports?**
-   `Envelope`, `Payload` - For creating Open Floor protocol messages
-   `GetManifestsEvent` - To request agent capabilities
-   `UtteranceEvent`, `DialogEvent`, `TextFeature` - For chat messages
-   `requests` - For HTTP communication with agents
-   `uuid` - To generate unique IDs for our client

### Step 1.2: Start the OpenFloorClient class

Now let's create our core client class:

```python
class OpenFloorClient:
    """
    A client for interacting with Open Floor Protocol agents
    Handles manifest discovery and chat functionality
    """
    
    def __init__(self, speaker_uri: Optional[str] = None, service_url: Optional[str] = None):
        self.speaker_uri = speaker_uri or f"client:{uuid.uuid4().hex[:8]}"
        self.service_url = service_url or "http://localhost:3000/"
        self.conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        print(f"🔗 Open Floor client initialized")
        print(f"   Speaker URI: {self.speaker_uri}")
        print(f"   Service URL: {self.service_url}")
```

**What we just did:**
-   Created a class to handle all Open Floor communication
-   Generated unique IDs for the client, conversation, and service
-   Added some friendly output to show the client is ready

### Step 1.3: Add envelope creation helper

Next, let's add a method to create properly formatted envelopes:

```python
    def _create_envelope(self, events: List[Any]) -> Envelope:
        """Create a properly formatted envelope for OpenFloor communication"""
    
        conversation = Conversation()
        sender = Sender(speakerUri=self.speaker_uri)
    
        envelope = Envelope(
            conversation=conversation,
            sender=sender,
            events=events
        )
    
        return envelope
```

**Why this helper?**
-   Every Open Floor message needs to be wrapped in an envelope
-   The envelope contains metadata about who's sending and the conversation
-   This keeps our code DRY (Don't Repeat Yourself)

### Step 1.4: Add network communication method

Now let's add the method that actually sends messages to agents:

```python
    def _send_envelope(self, envelope: Envelope, target_url: str) -> Dict[str, Any]:
        """Send an envelope to an agent and return the response"""
        
        # Create the payload
        payload = Payload(openFloor=envelope)
		payload_json = payload.to_json()
        payload_dict = json.loads(payload_json)
        
        try:
            print(f"📤 Sending request to: {target_url}")
            response = requests.post(
                target_url,
                json=payload_dict,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
```

**What this does:**
-   Wraps the envelope in a payload (as required by the protocol)
-   Sends an HTTP POST request with proper headers
-   Handles network errors and invalid JSON responses
-   Returns the parsed JSON response for further processing

### Step 1.5: Implement manifest fetching

Let's add the method to get agent capabilities:

```python
    def get_manifest(self, agent_url: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch the manifest from an Open Floor agent
        Returns the list of manifests or None if failed
        """
        
        print(f"🔍 Requesting manifest from: {agent_url}")
        
        try:
            # Create the getManifests event
            get_manifests_event = GetManifestsEvent(
                to=To(serviceUrl=agent_url)
            )
            
            # Create and send the envelope
            envelope = self._create_envelope([get_manifests_event])
            response_data = self._send_envelope(envelope, agent_url)
            
            # Parse the response to extract manifests
            if 'openFloor' in response_data:
                envelope_data = response_data['openFloor']
                events = envelope_data.get('events', [])
                
                for event in events:
                    if event.get('eventType') in ['publishManifests', 'publishManifest']:
                        parameters = event.get('parameters', {})
                        manifests = parameters.get('servicingManifests', [])
                        
                        if manifests:
                            print(f"✅ Found {len(manifests)} manifest(s)")
                            return manifests
                
                print("⚠️ No manifests found in response")
                return []
            else:
                print("⚠️ Invalid response format")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching manifest: {e}")
            return None
```

**The manifest discovery process:**
1.  Create a `GetManifestsEvent` targeting the agent
2.  Send it wrapped in an envelope
3.  Look for `publishManifests` events in the response
4.  Extract and return the manifest data

### Step 1.6: Implement message sending

Now let's add the method to send chat messages:

```python
    def send_message(self, agent_url: str, message: str) -> Optional[str]:
        """
        Send a text message to an Open Floor agent
        Returns the agent's response or None if failed
        """
        
        print(f"💬 Sending message: {message}")
        
        try:
            # Create the text feature
            text_feature = TextFeature(values=[message])
            
            # Create the dialog event
            dialog_event = DialogEvent(
                speakerUri=self.speaker_uri,
                features={"text": text_feature}
            )
            
            # Create the utterance event
            utterance_event = UtteranceEvent(
                dialogEvent=dialog_event,
                to=To(serviceUrl=agent_url)
            )
            
            # Create and send the envelope
            envelope = self._create_envelope([utterance_event])
            response_data = self._send_envelope(envelope, agent_url)
            
            # Parse the response to extract the reply
            if 'openFloor' in response_data:
                envelope_data = response_data['openFloor']
                events = envelope_data.get('events', [])
                
                for event in events:
                    if event.get('eventType') == 'utterance':
                        parameters = event.get('parameters', {})
                        dialog_event = parameters.get('dialogEvent', {})
                        features = dialog_event.get('features', {})
                        text_feature = features.get('text', {})
                        
                        # Try to extract text from different possible formats
                        if 'values' in text_feature and text_feature['values']:
                            response_text = text_feature['values'][0]
                        elif 'tokens' in text_feature and text_feature['tokens']:
                            tokens = text_feature['tokens']
                            response_text = ''.join(token.get('value', '') for token in tokens if 'value' in token)
                        else:
                            response_text = str(text_feature.get('value', ''))
                        
                        if response_text:
                            print(f"📨 Agent replied: {response_text}")
                            return response_text
                
                print("⚠️ No utterance response found")
                return "Agent sent no response"
            else:
                print("⚠️ Invalid response format")
                return None
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
```

**The chat message flow:**
1.  Create a `TextFeature` with the user's message
2.  Wrap it in a `DialogEvent` and then an `UtteranceEvent`
3.  Send it to the agent
4.  Parse the response to extract the agent's reply
5.  Handle different text formats that agents might use

### Step 1.7: Add manifest formatting helper

Finally, let's add a method to nicely format manifests for display:

```python
    def format_manifest(self, manifests: List[Dict[str, Any]]) -> str:
        """Format manifests for display"""
        if not manifests:
            return "No manifests available"
        
        formatted = []
        for i, manifest in enumerate(manifests):
            formatted.append(f"\n📋 Manifest {i + 1}:")
            
            # Identification info
            identification = manifest.get('identification', {})
            if identification:
                formatted.append(f"  Name: {identification.get('conversationalName', 'Unknown')}")
                formatted.append(f"  Organization: {identification.get('organization', 'Unknown')}")
                formatted.append(f"  Description: {identification.get('synopsis', 'No description')}")
                formatted.append(f"  Speaker URI: {identification.get('speakerUri', 'Unknown')}")
            
            # Capabilities
            capabilities = manifest.get('capabilities', [])
            if capabilities:
                formatted.append(f"  Capabilities: {len(capabilities)}")
                for j, capability in enumerate(capabilities):
                    formatted.append(f"    {j + 1}. Keywords: {', '.join(capability.get('keyphrases', []))}")
                    descriptions = capability.get('descriptions', [])
                    if descriptions:
                        formatted.append(f"       Description: {descriptions[0]}")
        
        return '\n'.join(formatted)
```

**Why format manifests?**
-   Raw JSON is difficult to read in the terminal
-   This creates a clean, hierarchical display
-   Shows the most important information first

## Step 2: Building the CLI Interface

Now let's create the actual command-line interface. Create a new file `cli_client.py`.

### Step 2.1: Add imports and setup

```python
#!/usr/bin/env python3

import argparse
import sys
from openfloor_client import OpenFloorClient
```

**What we're importing:**
-   `argparse` - For handling command-line arguments
-   `sys` - For system operations like exiting
-   Our custom `OpenFloorClient` class

### Step 2.2: Create the CLI class

```python
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
```

**What this sets up:**
-   Creates an instance of our Open Floor client
-   Tracks the current agent URL for convenience
-   Provides a helpful banner with available commands

### Step 2.3: Implement manifest command

```python
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
```

**This command:**
-   Fetches the manifest using our client
-   Formats and displays it nicely
-   Remembers the URL so you can chat without retyping it

### Step 2.4: Implement chat command

```python
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
```

**The chat loop:**
-   Prompts for user input continuously
-   Handles exit commands gracefully
-   Sends messages and displays responses
-   Handles Ctrl+C and EOF properly

### Step 2.5: Add interactive mode

```python
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
```

**Interactive mode features:**
-   Command parsing with arguments
-   Remembers the last agent URL
-   Graceful error handling
-   Help system

### Step 2.6: Add command-line argument support

```python
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
```

**Command-line support:**
-   Direct commands: `python cli_client.py manifest <url>`
-   Interactive mode: `python cli_client.py` (no arguments)
-   Proper argument validation

## Step 3: Making it Executable

Make your CLI script executable:

```bash
chmod +x cli_client.py
```

## Step 4: Testing Your CLI Client

### Interactive mode:

```bash
python cli_client.py
```

**Try these commands:**

```
> manifest https://kmhhywpw32.us-east-1.awsapprunner.com/
> chat https://kmhhywpw32.us-east-1.awsapprunner.com/
```

### Direct commands:

```bash
# Get a manifest
python cli_client.py manifest https://kmhhywpw32.us-east-1.awsapprunner.com/

# Start a chat session
python cli_client.py chat https://kmhhywpw32.us-east-1.awsapprunner.com/
```

## Final Project Structure

Your project should now look like this:

```
openfloor-cli-client/
├── requirements.txt
├── openfloor_client.py    # Core Open Floor logic
└── cli_client.py          # CLI interface
```

## Testing with Sample Agents

Try these example Open Floor agents:

**Parrot Agent (echoes your messages):**

```
https://kmhhywpw32.us-east-1.awsapprunner.com/
```

**Verity Assistant (verifies your statements):**

```
https://secondassistant.pythonanywhere.com/verity
```