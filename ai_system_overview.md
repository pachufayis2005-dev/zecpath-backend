\# ZecPath AI System Overview



\## 1. Introduction



The ZecPath backend contains an AI-assisted interview system designed to support candidate evaluation during the hiring process.



The AI system is integrated with the Django REST Framework backend and is responsible for interview question generation, interview processing, answer evaluation, scoring, and feedback generation.



\---



\## 2. AI System Architecture



The main AI flow is:



Candidate

↓

Application

↓

InterviewCall

↓

AIInterviewSession

↓

AIQuestion

↓

AIAnswer

↓

Answer Submission

↓

Answer Evaluation

↓

Scoring Engine

↓

Final Score + AI Feedback

↓

AI Event Logging



\---



\## 3. AI Service Layer



The main AI integration layer is:



`core/services/ai\_bridge.py`



The `AIBridgeService` acts as a central bridge between the Django backend and external AI providers.



Current supported operations include:



\* Interview question generation

\* Speech-to-text processing

\* Text-to-speech processing

\* AI voice call triggering

\* AI interview startup



The current implementation uses simulated responses so that the backend architecture can later be connected to real AI providers.



\---



\## 4. Interview Question Generation



The AI bridge provides question generation based on the job title.



Example:



```text

Job Title

&#x20;  ↓

AIBridgeService

&#x20;  ↓

AI-generated interview question

```



The current implementation generates a simulated question such as:



"What interests you about the Backend Developer role?"



\---



\## 5. Answer Submission



Candidates submit answers through:



`POST /api/ai-answer/<answer\_id>/submit/`



The request contains the candidate's answer.



The backend validates the request using `SubmitAnswerSerializer`.



The validated answer is stored in the corresponding `AIAnswer` record.



\---



\## 6. Answer Evaluation



Answer evaluation is handled by:



`core/services/answer\_evaluator.py`



The `AnswerEvaluator` uses the `ScoringEngine` to calculate:



\* Relevance score

\* Completeness score

\* Confidence score

\* Final score

\* Matched keywords



The evaluator also generates feedback and records the evaluation timestamp.



\---



\## 7. Scoring Process



The scoring flow is:



```text

Candidate Answer

&#x20;      ↓

Keyword / Relevance Analysis

&#x20;      ↓

Completeness Analysis

&#x20;      ↓

Confidence Analysis

&#x20;      ↓

Final Score

```



The result is stored in the `AIAnswer` model.



The system stores:



\* `relevance\_score`

\* `completeness\_score`

\* `confidence\_score`

\* `final\_score`

\* `matched\_keywords`

\* `ai\_feedback`

\* `evaluated\_at`



\---



\## 8. Example AI Evaluation Result



Example successful evaluation:



```json

{

&#x20;   "question": "Tell me about yourself.",

&#x20;   "relevance\_score": 28.57,

&#x20;   "completeness\_score": 60.0,

&#x20;   "confidence\_score": 100.0,

&#x20;   "final\_score": 52.28,

&#x20;   "matched\_keywords": \[

&#x20;       "django",

&#x20;       "rest"

&#x20;   ],

&#x20;   "feedback": "Matched 2 keyword(s). Overall score: 52.28"

}

```



This demonstrates that the backend successfully processes an interview answer and produces structured evaluation results.



\---



\## 9. AI Event Logging



AI-related events are recorded using the AI event logging service.



The backend contains:



`AIEventLog`



and:



`core/services/logging\_service.py`



This provides traceability for important AI interview events and evaluations.



\---



\## 10. Security and Access Control



The AI APIs use authentication and authorization mechanisms.



The backend includes:



\* JWT authentication

\* Role-based access control

\* Ownership validation

\* Login throttling

\* User throttling

\* Security logging

\* Audit trails



Failure testing was also performed.



For example, unauthorized access produced:



```json

{

&#x20;   "error": "Permission denied"

}

```



This confirms that ownership validation is active for protected AI resources.



\---



\## 11. Failure Handling



The AI system and supporting APIs were tested against failure scenarios including:



\* Invalid authentication

\* Missing authentication

\* Unauthorized resource access

\* Invalid requests

\* Missing AI answer records

\* Invalid API parameters

\* Permission violations



The backend returns appropriate HTTP error responses instead of exposing internal application data.



\---



\## 12. Load Testing



Locust was used to perform backend load testing.



The Locust test covers:



\* Login

\* Job listing

\* Latest jobs

\* Featured jobs



This provides an initial performance check for authenticated API access.



\---



\## 13. Current AI Integration Status



The AI architecture is prepared for integration with external providers.



The current `AIBridgeService` uses simulated AI responses.



Future integrations can replace the simulated methods with real services such as:



\* AI language models

\* Speech-to-text providers

\* Text-to-speech providers

\* Voice-call providers



The service-layer abstraction allows these integrations to be added without redesigning the complete backend architecture.



\---



\## 14. Production Readiness Summary



The ZecPath backend currently contains the major components required for the AI-assisted hiring workflow:



\* Authentication

\* Authorization

\* Job management

\* Applications

\* AI interview sessions

\* AI questions

\* AI answers

\* Answer evaluation

\* Candidate scoring

\* AI feedback

\* Interview scheduling

\* Reminders

\* Analytics

\* Audit logging

\* Security logging

\* Load testing



The backend architecture is organized into API, model, serializer, security, and service layers.



The AI provider integration remains simulated and should be replaced with production AI providers before real-world deployment.



\---



\## 15. Conclusion



The AI backend provides an end-to-end foundation for an AI-assisted hiring platform.



The system can accept interview answers, evaluate them using multiple scoring components, generate structured feedback, protect candidate resources through authorization checks, and record AI-related events for traceability.



The architecture is designed so that external AI providers can be integrated later through the centralized AI bridge service.



