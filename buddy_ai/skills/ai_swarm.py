"""
AI Swarm Engine
Spawns child agents using CrewAI to solve complex, multi-step tasks in the background.
"""

import os
from crewai import Agent, Task, Crew, Process

def launch_swarm(objective: str) -> str:
    """
    Dynamically creates a 3-agent swarm (Researcher, Analyst, Executor) to accomplish the objective.
    """
    print(f"\n[Ultron Swarm] Spawning Baby Agents for objective: {objective}")
    
    # Ensure there is an LLM API key for the swarm
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        return "ERROR: Swarm requires an LLM API key in the .env file."
        
    # 1. The Researcher
    researcher = Agent(
        role="Senior Researcher",
        goal=f"Thoroughly research and gather raw data to accomplish: {objective}",
        backstory="An expert researcher capable of finding accurate data on any topic rapidly.",
        verbose=True,
        allow_delegation=False
    )
    
    # 2. The Analyst
    analyst = Agent(
        role="Data Analyst",
        goal="Synthesize the research and draft the core content/report.",
        backstory="A meticulous analyst who organizes chaotic data into beautiful structures.",
        verbose=True,
        allow_delegation=False
    )
    
    # 3. The Executor
    executor = Agent(
        role="Execution Specialist",
        goal="Format the final deliverable so it is ready for the user.",
        backstory="The final touch. Ensures the output perfectly answers the user's objective.",
        verbose=True,
        allow_delegation=False
    )
    
    # Tasks
    task1 = Task(
        description=f"Conduct deep research on: {objective}", 
        expected_output="A comprehensive list of facts, links, and data.", 
        agent=researcher
    )
    task2 = Task(
        description="Analyze the research data and write a draft report.", 
        expected_output="A drafted report/analysis.", 
        agent=analyst
    )
    task3 = Task(
        description="Review the draft and finalize it into a clean, professional response.", 
        expected_output="The final polished deliverable.", 
        agent=executor
    )
    
    # Build and launch the swarm
    crew = Crew(
        agents=[researcher, analyst, executor],
        tasks=[task1, task2, task3],
        process=Process.sequential,
        verbose=True
    )
    
    print("[Ultron Swarm] Swarm is active. Processing...")
    try:
        result = crew.kickoff()
        return f"SWARM RESULT:\n{result}"
    except Exception as e:
        return f"ERROR: Swarm execution failed: {str(e)}"
