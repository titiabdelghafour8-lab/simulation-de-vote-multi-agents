import os
import random
import time
import uuid
import json
import logging
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import concurrent.futures
from collections import Counter
from database import DatabaseManager

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class VoteAction(BaseModel):
    ranked_candidates: List[str] = Field(description="A list ranking your top 3 choices: ['Candidate A', 'Candidate B', 'Candidate C']. Must strictly be the exact names of the candidates.")
    reasoning: str = Field(description="Brief explanation of why you ranked them this way.")
    confidence: int = Field(description="An integer from 1 to 100 representing how confident you are in your 1st choice.")

class VoterAgent:
    """Represents a single voter in the simulation."""
    def __init__(self, agent_id, person):
        self.agent_id = agent_id
        self.person = person

class Orchestrator:
    """Manages the Delphi Method voting simulation rounds and agents."""
    def __init__(self):
        self.db = DatabaseManager() 
        self.run_id = str(uuid.uuid4())
        
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)
        self.brain = self.llm.with_structured_output(VoteAction)
        
        # Load configuration
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.manifestos = config["manifestos"]
                base_person = config["personas"]
        except Exception as e:
            logger.error(f"Failed to load config.json: {e}")
            raise e

        self.voters = []
        for i in range(1, 31):
            agent_id = f"Votant_{i:02d}"
            assigned_person = random.choice(base_person) 
            self.voters.append(VoterAgent(agent_id, assigned_person))

    def robust_llm_call(self, llm_or_brain, messages, max_retries=5):
        """Wrapper around LLM calls with exponential backoff for rate limits."""
        base_delay = 2.0
        for attempt in range(max_retries):
            try:
                return llm_or_brain.invoke(messages)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"API Error. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)

    def summarize_arguments(self, reasonings):
        """Uses LLM to summarize the arguments from the previous round."""
        prompt = f"Here are the reasonings provided by voters in the last round:\n{reasonings}\n\nPlease provide a concise summary of the main arguments for and against each candidate. Group them by candidate."
        sys_msg = SystemMessage(content="You are an impartial facilitator summarizing arguments from a Delphi voting panel.")
        human_msg = HumanMessage(content=prompt)
        return self.robust_llm_call(self.llm, [sys_msg, human_msg]).content

    def process_vote(self, voter, round_num, previous_round_summary=None, previous_round_tallies=None):
        """Executes a single vote action for a single agent."""
        try:
            sys_msg_content = f"Role: {voter.person}. Read manifestos and rank the candidates 1st, 2nd, and 3rd. IMPORTANT: Provide your 'reasoning' strictly in English and do NOT use any apostrophes or special characters to prevent JSON formatting errors."
            if round_num > 1:
                sys_msg_content += f"\n\nThis is Round {round_num} of the Delphi method. Here are the voting results and the summary of arguments from the previous round. Review the group's feedback. You may change your vote and reasoning if persuaded, or keep it the same."
                human_msg_content = f"Manifestos:\n{self.manifestos}\n\nPrevious Round Tallies:\n{previous_round_tallies}\n\nPrevious Round Arguments Summary:\n{previous_round_summary}"
            else:
                sys_msg_content += "\n\nThis is Round 1. Vote truthfully for your favorite candidate based on the manifestos."
                human_msg_content = f"Manifestos:\n{self.manifestos}"

            sys_msg = SystemMessage(content=sys_msg_content)
            human_msg = HumanMessage(content=human_msg_content)
            
            decision = self.robust_llm_call(self.brain, [sys_msg, human_msg])
            self.db.save_vote(self.run_id, voter.agent_id, voter.person, decision.ranked_candidates, decision.reasoning, decision.confidence, round_num)
            
            return decision
        except Exception as e:
            logger.error(f"Erreur avec {voter.agent_id}: {e}")
            return None

    def run(self):
        """Runs the main orchestrator loop."""
        logger.info(f"🚀 Lancement de l'Orchestrateur (Delphi Method) | Run ID: {self.run_id}")
        
        MAX_ROUNDS = 4
        CONSENSUS_THRESHOLD = 0.75
        
        previous_round_summary = None
        previous_round_tallies = None
        
        for round_num in range(1, MAX_ROUNDS + 1):
            logger.info(f"--- 🔄 Round {round_num} ---")
            
            decisions = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(self.process_vote, v, round_num, previous_round_summary, previous_round_tallies): v for v in self.voters}
                for future in concurrent.futures.as_completed(futures):
                    decision = future.result()
                    voter = futures[future]
                    if decision:
                        decisions.append(decision)
                        logger.info(f"✅ {voter.agent_id} a voté: {decision.ranked_candidates[0] if decision.ranked_candidates else 'None'} (1er choix, Confiance: {decision.confidence}%)")
            
            if not decisions:
                logger.error("No decisions were made due to errors. Aborting.")
                break
                
            # Aggregate Poll Results
            first_choices = [d.ranked_candidates[0] for d in decisions if d.ranked_candidates]
            poll_tally = Counter(first_choices)
            total_votes = len(first_choices)
            poll_summary = "\n".join([f"{cand}: {count} votes ({(count/total_votes)*100:.1f}%)" for cand, count in poll_tally.items()])
            logger.info(f"\n📈 Résultats du Round {round_num} :\n{poll_summary}\n")
            
            # Check Consensus
            top_candidate, top_votes = poll_tally.most_common(1)[0]
            if top_votes / total_votes >= CONSENSUS_THRESHOLD:
                logger.info(f"🎉 Consensus atteint ! {top_candidate} a {top_votes}/{total_votes} voix ({(top_votes/total_votes)*100:.1f}%).")
                break
            elif round_num == MAX_ROUNDS:
                logger.warning("⚠️ Nombre maximum de rounds atteint sans consensus absolu.")
                break
            else:
                logger.info("⏳ Consensus non atteint. Préparation du prochain round...")
                all_reasonings = "\n".join([f"- {d.reasoning}" for d in decisions])
                logger.info("🤖 Génération du résumé des arguments pour le prochain round...")
                previous_round_summary = self.summarize_arguments(all_reasonings)
                previous_round_tallies = poll_summary
                
        logger.info("🏁 Simulation terminée !")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()