import yaml
import os
class Agent:
    # Class variable to store message history
    messages = []

    def __init__(self, agent_name):        
        self.assets_needed = []
        self.parse_instructions(agent_name)
        return None

    def parse_instructions(self, agent_name):
        """
        There is a file called system_instruction/{agent_name}.yml.
        Parase the variables in it and create them as instance variables.
        """
        path = os.path.join(os.path.dirname(__file__), 'system_instructions', f'{agent_name}.yaml')
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                instructions = yaml.load(f, Loader=yaml.FullLoader)
            # Parse the variables
            for key in instructions:
                setattr(self, key, instructions[key])
        else:
            raise FileNotFoundError(f'No system instruction found for {agent_name}.')


    def get_instance_vars(self):
        """
        Returns a dictionary of instance variables
        """
        return self.__dict__

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
    def __init__(self, system_instruction, default_model, temperature, max_tokens):
        super().__init__(system_instruction, default_model, temperature, max_tokens)
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
