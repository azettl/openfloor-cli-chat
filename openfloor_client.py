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
                    if event.get('eventType') == 'publishManifests':
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