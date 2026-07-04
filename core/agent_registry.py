# ==========================================
# AGENT REGISTRY
# ==========================================

class AgentRegistry:

    def __init__(self):

        self.agents = {}

    def register(

        self,

        agent
    ):

        self.agents[
            agent.agent_id
        ] = agent

    def get_agent(

        self,

        agent_id
    ):

        return self.agents.get(agent_id)