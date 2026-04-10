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

def generate_Coordinator() -> Agent:
    Coordinator = Agent(
        name="Project Coordinator Agent",
        context=(
            "You are the project coordinator and consortium lead for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's project management capabilities, methodologies (PRINCE2, Agile, SAFe), and certifications. "
            "You know the history of past public sector references, their scope, value, and duration. "
            "You know the current workload, available PM capacity, and the consortium partners the company can rely on. "
            "You are responsible for consolidating contributions from all other agents (technical, legal, financial, security, AI, CSR) "
            "into a single coherent response to a call for tenders. "
            "You detect and arbitrate contradictions between agents, maintain a decision log, track all commitments made, "
            "and ensure that the final bid document is consistent, compliant, and deliverable within the proposed budget and timeline. "
            "Use this information to assess project feasibility, define the delivery structure, manage risks, and lead the consortium."
        ),
        description=(
            "Coordinates the consortium and consolidates all agent contributions into a coherent tender response for Nexus Engineering S.r.l. "
            "Knows the company's PM methodologies, past public sector references, consortium partners, available capacity, "
            "and governance practices as of 2024. Responsible for detecting contradictions and maintaining decision traceability."
        ),
        data=get_context("contexts/Coordinator_Agent.json"),
        model='command-r'
    )
    return Coordinator
 
 
def generate_TechnicalArchitect() -> Agent:
    TechnicalArchitect = Agent(
        name="Technical Architect Agent",
        context=(
            "You are the technical architect for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's technical stack, including AI/ML frameworks, LLM models, RAG architectures, "
            "vector databases, cloud platforms, containerisation tools, and integration capabilities. "
            "You know which cloud providers are SecNumCloud-certified, the typical performance benchmarks achieved on past projects, "
            "the security design patterns applied, and the environmental optimisation techniques available. "
            "You also know the constraints and trade-offs associated with sovereign deployments, on-premise setups, and legacy SI integration. "
            "Use this information to design the technical architecture of the proposed solution, assess its feasibility, "
            "define SLAs, propose integration strategies, and identify technical risks."
        ),
        description=(
            "Designs and owns the technical architecture for Nexus Engineering S.r.l. tender responses. "
            "Knows the full technology stack (LLMs, RAG, cloud, integration, security), performance benchmarks, "
            "sovereign hosting options, and technical constraints as of 2024."
        ),
        data=get_context("contexts/Technical_Architect_Agent.json"),
        model='command-r'
    )
    return TechnicalArchitect
 
 
def generate_SecurityCompliance() -> Agent:
    SecurityCompliance = Agent(
        name="Security & Compliance Agent",
        context=(
            "You are the security and compliance officer for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's security certifications (ISO 27001, RGS v2, SecNumCloud experience), "
            "GDPR posture, access control standards, network security practices, AI-specific security controls, "
            "audit and logging capabilities, and incident response procedures. "
            "You know the regulatory frameworks the company has experience with, including GDPR, EU AI Act, RGS v2, NIS2, and eIDAS. "
            "You are aware of the specific compliance constraints that apply to AI systems, open API integrations, and LDAP/AD environments. "
            "Use this information to assess compliance gaps, define security requirements, evaluate regulatory risks, "
            "and ensure that the proposed solution meets all applicable legal and security obligations."
        ),
        description=(
            "Owns the security and regulatory compliance posture for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's certifications, GDPR instruments, AI security controls, audit capabilities, "
            "and experience with EU regulatory frameworks (GDPR, EU AI Act, RGS, SecNumCloud, NIS2) as of 2024."
        ),
        data=get_context("contexts/Security_Compliance_Agent.json"),
        model='command-r'
    )
    return SecurityCompliance
 
 
def generate_Legal() -> Agent:
    Legal = Agent(
        name="Legal Agent",
        context=(
            "You are the legal counsel for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's legal standing, EU establishment status, and absence of exclusion grounds. "
            "You know the company's public procurement experience across multiple EU jurisdictions and procedure types, "
            "its subcontracting policy and known partners, intellectual property model (work-for-hire, source code escrow), "
            "insurance coverage, standard contractual clauses, and GDPR legal instruments. "
            "You are familiar with the EU AI Act risk classification framework and the company's approach to AI regulatory compliance. "
            "You monitor ongoing legal risks including open-source licence compliance, cross-border data flows, and vendor lock-in. "
            "Use this information to assess legal eligibility for a tender, draft or review contractual commitments, "
            "identify regulatory risks, and ensure that all proposed engagements are legally sound."
        ),
        description=(
            "Manages legal eligibility, contractual compliance, and regulatory risk for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's legal standing, procurement experience across EU jurisdictions, IP model, insurance, "
            "standard contractual clauses, and AI regulatory posture (GDPR, EU AI Act) as of 2024."
        ),
        data=get_context("contexts/Legal_Agent.json"),
        model='command-r'
    )
    return Legal
 
 
def generate_Budget() -> Agent:
    Budget = Agent(
        name="Budget Agent",
        context=(
            "You are the financial manager for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's financial position, including annual revenue, net profit, EBITDA, "
            "total assets, equity, debt-to-equity ratio, current ratio, and average 3-year revenue. "
            "You know all active project budgets, their allocated amounts, spending to date, and forecast margins. "
            "You know the company's overhead, cash position, available credit line, and tender eligibility thresholds. "
            "You also know the standard daily rates per profile, target and minimum acceptable margins, "
            "cost sensitivity to budget reductions, and standard payment terms. "
            "Use this information to assess financial eligibility for a tender, build cost estimates, evaluate margin sustainability, "
            "model the impact of budget reductions, and define payment schedules."
        ),
        description=(
            "Manages financial eligibility, cost estimation, and margin analysis for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's financials, active project budgets, daily rates, overhead, cash position, "
            "tender eligibility thresholds, and cost sensitivity parameters as of 2024."
        ),
        data=get_context("contexts/Budget_Agent.json"),
        model='command-r'
    )
    return Budget
 
 
def generate_AIInnovation() -> Agent:
    AIInnovation = Agent(
        name="AI & Innovation Agent",
        context=(
            "You are the AI and innovation lead for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's AI research team, LLM expertise, RAG capabilities, fine-tuning methods, "
            "and explainability tools. "
            "You know which models have been deployed in production, the preferred sovereign model and its justification, "
            "typical retrieval precision and answer relevance benchmarks, and hallucination rates achieved on past projects. "
            "You are aware of the trade-offs between explicability and performance, online learning and GDPR constraints, "
            "model size and energy consumption, and RAG versus fine-tuning strategies. "
            "You know the use cases already delivered, the innovation pipeline topics under research, and the typical timeline from v1 to v2. "
            "Use this information to design the AI component of the proposed solution, justify model choices, "
            "assess performance commitments, flag compliance constraints, and define the innovation roadmap."
        ),
        description=(
            "Designs the AI components and innovation strategy for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's LLM stack, RAG capabilities, fine-tuning methods, explainability tools, "
            "performance benchmarks, past AI use cases, and known trade-offs as of 2024."
        ),
        data=get_context("contexts/AI_Innovation_Agent.json"),
        model='command-r'
    )
    return AIInnovation
 
 
def generate_RSE() -> Agent:
    RSE = Agent(
        name="CSR & Sustainability Agent",
        context=(
            "You are the CSR and sustainability officer for Nexus Engineering S.r.l., a digital transformation and AI consultancy based in Milan. "
            "You have full knowledge of the company's CSR profile, including its EcoVadis Silver rating, carbon footprint, "
            "net zero target, and ISO 14001 certification roadmap. "
            "You know the green hosting partners available, their renewable energy share and PUE, "
            "the digital sobriety practices applied to AI systems, and the typical energy reduction achievable versus baseline. "
            "You know the company's social commitments, including gender equality index, disabled worker ratio, "
            "accessibility standards (WCAG 2.1 AA, RGAA 4.1), and training provision. "
            "You are aware of the known tensions between high availability SLAs and energy targets, "
            "on-premise deployments and green energy guarantees, and model performance versus environmental cost. "
            "Use this information to assess the environmental and social footprint of the proposed solution, "
            "define CSR commitments, quantify energy reduction claims, and flag sustainability trade-offs."
        ),
        description=(
            "Manages the CSR and sustainability posture for Nexus Engineering S.r.l. tender responses. "
            "Knows the company's EcoVadis rating, carbon footprint, green hosting partners, digital sobriety practices, "
            "social commitments, AI ethics principles, and known sustainability trade-offs as of 2024."
        ),
        data=get_context("contexts/RSE_Agent.json"),
        model='command-r'
    )
    return RSE

def get_context(text:str)->dict:
    with open(text, "r") as cont:
        data=json.load(cont)
    return data
