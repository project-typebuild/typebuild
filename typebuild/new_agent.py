import yaml
import os
class Agent:
    # Class variable to store message history

    def __init__(self, agent_name):        
        self.assets_needed = []
        self.messages = []
        self.parse_instructions(agent_name)
        return None

    def get_message(self, message):
        # Add message to the class-wide message history
        self.messages.append(message)
        # Optionally, limit the history to last 'k' messages
        # cls.messages = cls.messages[-k:]

    def get_system_instruction(self):
        """
        Returns the system instruction
        """
        return self.system_instruction

    
    def parse_instructions(self, agent_name):
        """
        There is a file called system_instruction/{agent_name}.yml.
        Parase the variables in it and create them as instance variables.
        """
        path = os.path.join(os.path.dirname(__file__), 'system_instructions', f'{agent_name}.yml')
        
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

    def send_response_to_chat_framework(self):
        """
        Sends all the chat messages or the final message to the chat framework
        """
        pass

    def respond(self):
        # Implement the response logic
        # This can involve using the default_model, temperature, and max_tokens
        # to generate a response based on the current message history and assets
        pass

class AgentManager(Agent):
    def __init__(self, agent_name):
        super().__init__(agent_name)
        self.managed_agents = {}

    def add_agent(self, agent_name, agent):
        self.managed_agents[agent_name] = agent

    def get_system_instruction(self, agent_name):
        """
        Add the agent name and description to the system instructions
        """
        if agent_name in self.managed_agents:
            instruction = self.managed_agents[agent_name].get_system_instruction()
        else:
            instruction = self.system_instruction
            instruction += "The following agents are available:\n"
            for agent_name, agent in self.managed_agents.items():
                instruction += f"{agent_name}: {agent.description}"

        return instruction

    def get_model(self, agent_name):
        """
        Returns the model for the agent
        """
        if agent_name in self.managed_agents:
            model = self.managed_agents[agent_name].default_model
        else:
            model = self.default_model
        return model
    
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



