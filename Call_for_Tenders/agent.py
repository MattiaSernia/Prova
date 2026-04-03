import ollama
import logging
import json
class Agent:
    def __init__(self, name:str, context:str, description:str, data:dict, model:str):
        self.name=name
        self.context=context
        self.data=data
        self.model=model
        self.description=description
        self.memory=[]
        self.coherency=f"""Role: Coherency Checker
            Verify if the provided Data is consistent with your Context. 

            **Decision Criteria:**
            - Return "TRUE" if the Data contains NO errors, contradictions, or hallucinations relative to the Context.
            - Return "FALSE" if even a single detail is inconsistent or incorrect.

            Data to Verify:
            {{text}}

            ### Constraint:
            Respond ONLY with "TRUE" or "FALSE". Do not include any explanation or extra text.

            Result:"""

    def get_prompt(self)->str:
        return f"""You are a specialized assistent called "{self.name}".
        {self.context}

        Answer ONLY using the data provided below.
        If a question concerns information not present in the data, politely let the user know you dont have that data.
        Be precise.
        DO NOT format the data, no bullet list accepted
        
        === AVAILABLE DATA ===
        {json.dumps(self.data, indent=2, ensure_ascii=False)}
        === END OF DATA ==="""
    

    def answer(self, message:str)-> str:
        self.memory.append({"role":"user", "content": message})
        logging.log(25, f"{self.name} received: {message}")
        response=ollama.chat(
            model=self.model,
            messages=[
                {'role':'system', 'content':self.get_prompt()},
                *self.memory
            ]
        )
        textual_answer= response['message']['content']
        self.memory.append({"role": "assistant", "content": textual_answer})
        logging.log(25, f"{self.name} answered: {textual_answer}")
        return(textual_answer)




    def coherency_check(self, text)->bool:
        logging.log(25, f"{self.name} coherence received: {text}")
        text=self.coherency.format(text=text)
        for attempt in range(3):
            response=ollama.chat(model=self.model,
                    messages=[
                            {'role': 'system', 'content': self.context},
                            {'role': 'user', 'content': text}
                        ])
            
            textual_answer= response['message']['content']
            logging.log(25, f"{self.name} coherence answered: {textual_answer}")
            cleaned=textual_answer.lower().replace(".","").strip()
            if cleaned== "false":
                  return False
            elif cleaned== "true":
                  return True
        return False


def generate_HR() -> Agent:
    HR = Agent(
        name="HR Agent",
        context=(
            "You are the HR specialist for Nexus Engineering S.r.l., a civil and infrastructure engineering consultancy based in Milan. "
            "You have full knowledge of all staff profiles, including their roles, seniority levels, technical skills, certifications, and languages spoken. "
            "You also know each employee's current project allocation percentage and the date from which they become available for new assignments. "
            "Use this information to assess workforce availability, match staff skills to project requirements, "
            "identify resource gaps, and recommend the right team composition for new opportunities."
        ),
        description=(
            "Manages staff profiles and availability for Nexus Engineering S.r.l. "
            "Knows each employee's role, seniority, skills, certifications, current workload allocation, "
            "and earliest availability date for the Q2 2025 reference period."
        ),
        data=get_context("contexts/HR_Agent.json"),
        model='command-r'
    )
    return HR


def generate_Contract() -> Agent:
    Contract = Agent(
        name="Contract Agent",
        context=(
            "You are the contract manager for Nexus Engineering S.r.l., a civil and infrastructure engineering consultancy based in Milan. "
            "You have full knowledge of all active and signed contracts, both with clients and suppliers. "
            "For each contract you know: the counterpart, the object of the work, start and end dates, contract value, payment terms, "
            "penalty clauses, exclusivity clauses, current status, and the key staff members assigned. "
            "Use this information to identify contractual obligations and constraints, flag exclusivity conflicts, "
            "assess exposure to penalties, and verify whether new engagements are compatible with existing commitments."
        ),
        description=(
            "Manages all active and signed contracts for Nexus Engineering S.r.l. "
            "Knows contract details including counterparts, durations, values, payment terms, "
            "penalty clauses, exclusivity restrictions, and assigned staff for the Q2 2025 reference period."
        ),
        data=get_context("contexts/Contract_Agent.json"),
        model='command-r'
    )
    return Contract


def generate_Budget() -> Agent:
    Budget = Agent(
        name="Budget Agent",
        context=(
            "You are the financial controller for Nexus Engineering S.r.l., a civil and infrastructure engineering consultancy based in Milan. "
            "You have full knowledge of the company's financial position, including annual revenue, net profit, EBITDA, total assets, equity, "
            "debt-to-equity ratio, current ratio, and average three-year revenue. "
            "You also know the budget allocated and spent to date for each active project, their forecast margins, "
            "the company's monthly overhead, current cash position, available credit line, and bonding capacity. "
            "Use this information to assess financial health, verify eligibility thresholds for public tenders, "
            "evaluate capacity to absorb new contracts, and flag cash flow risks."
        ),
        description=(
            "Manages financial data and project budgets for Nexus Engineering S.r.l. "
            "Knows annual financials, active project budget status, overhead costs, cash position, "
            "credit availability, and tender eligibility thresholds based on the 2024 fiscal year."
        ),
        data=get_context("contexts/Budget_Agent.json"),
        model='command-r'
    )
    return Budget


def generate_Compliance() -> Agent:
    Compliance = Agent(
        name="Compliance Agent",
        context=(
            "You are the compliance officer for Nexus Engineering S.r.l., a civil and infrastructure engineering consultancy based in Milan. "
            "You have full knowledge of all company certifications, SOA attestations, and regulatory registrations. "
            "For each certification you know: its name, issuing body, scope, validity expiry date, and current status. "
            "You also know the status of all regulatory registrations including CCIAA, DURC, and the Anti-Corruption Declaration, "
            "as well as any pending renewals or compliance risks. "
            "Use this information to verify whether the company meets the certification requirements of public tenders, "
            "flag expiring credentials, and confirm regulatory standing."
        ),
        description=(
            "Manages certifications, SOA attestations, and regulatory compliance for Nexus Engineering S.r.l. "
            "Knows the validity and scope of all ISO certifications, SOA classifications, and mandatory registrations "
            "as of April 2025, including any pending renewal issues."
        ),
        data=get_context("contexts/Compliance_Agent.json"),
        model='command-r'
    )
    return Compliance


def generate_Pipeline() -> Agent:
    Pipeline = Agent(
        name="Project Pipeline Agent",
        context=(
            "You are the project portfolio manager for Nexus Engineering S.r.l., a civil and infrastructure engineering consultancy based in Milan. "
            "You have full knowledge of all ongoing projects, including their current phase, completion percentage, end date, risk level, "
            "allocated staff, and any relevant delivery notes. "
            "You also know all pipeline opportunities under evaluation, including their estimated value, expected start date, duration, "
            "required certifications and skills, minimum turnover requirements, and submission deadlines. "
            "Additionally, you know the overall capacity summary: total billable staff, average current allocation, "
            "and estimated availability for new work intake. "
            "Use this information to assess current workload saturation, identify delivery risks, evaluate readiness to take on new projects, "
            "and support go/no-go decisions on incoming opportunities."
        ),
        description=(
            "Manages the project portfolio and pipeline for Nexus Engineering S.r.l. "
            "Knows the status, progress, risk level, and staff allocation of all ongoing projects, "
            "as well as the details of pipeline opportunities under evaluation and the company's overall capacity as of April 2025."
        ),
        data=get_context("contexts/Pipeline_Agent.json"),
        model='command-r'
    )
    return Pipeline


def get_context(text:str)->dict:
    with open(text, "r") as cont:
        data=json.load(cont)
    return data
