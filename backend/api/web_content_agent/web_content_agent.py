from agency_swarm import Agent

class WebContentAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WebContentAgent",
            description="Web içeriği üretme ve SEO açısından optimize etme konusunda uzman bir acente.",
            instructions="instructions.md",
            tools=[
                # WebContentGenerator,
                # WebContentOptimizer
            ]
        )
