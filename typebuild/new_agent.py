import yaml
import os
class Agent:
    # Class variable to store message history
    messages = []

    def __init__(self, system_instruction, default_model, temperature, max_tokens, assets_needed):
        self.system_instruction = system_instruction
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.assets_needed = assets_needed

    @classmethod
    def receive_message(cls, message):
        # Add message to the class-wide message history
        cls.messages.append(message)
        # Optionally, limit the history to last 'k' messages
        # cls.messages = cls.messages[-k:]

    def process_request(self):
        # Process the request based on the assets needed
        # Access the class variable messages as needed
        # Implement logic to use system_instruction, default_model, etc.
        pass

    def respond(self):
        # Implement the response logic
        # This can involve using the default_model, temperature, and max_tokens
        # to generate a response based on the current message history and assets
        pass

class AgentManager(Agent):
    def __init__(self, system_instruction, default_model, temperature, max_tokens, assets_needed):
        super().__init__(system_instruction, default_model, temperature, max_tokens, assets_needed)
        self.managed_agents = {}

    def add_agent(self, agent_name, agent):
        self.managed_agents[agent_name] = agent

    def remove_agent(self, agent_name):
        if agent_name in self.managed_agents:
            del self.managed_agents[agent_name]

    def distribute_message(self, message):
        for agent in self.managed_agents.values():
            agent.receive_message(message)

    def collect_responses(self):
        responses = {}
        for agent_name, agent in self.managed_agents.items():
            responses[agent_name] = agent.respond()
        return responses


# Override or extend methods from Agent as needed


def system_instruction_for_agents(agent_name):
    """
    Read the system instruction from the yaml file and return it as a string, by taking agent name as input
    """

    path = os.path.join(os.path.dirname(__file__), 'system_instructions', f'{agent_name}.yaml')
        
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)['instruction']

    else:
        raise FileNotFoundError(f'No system instruction found for {agent_name}.')
