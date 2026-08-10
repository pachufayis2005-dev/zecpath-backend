\# ZecPath Subscription Feature Access Mapping



\## 1. Overview



ZecPath uses a subscription-based SaaS monetization model for employer and recruiter features.



The subscription system contains three plans:



\* FREE

\* PRO

\* ENTERPRISE



The subscription level determines which employer features and APIs are available.



\---



\## 2. Subscription Plans



\### FREE Plan



The Free plan provides limited access to employer functionality.



Features:



\* Limited job postings

\* Limited AI interviews

\* No recruiter analytics

\* No AI analytics

\* No featured job functionality



\---



\### PRO Plan



The Pro plan provides expanded recruiter functionality.



Features:



\* Unlimited job postings

\* Higher AI interview limit

\* Recruiter analytics

\* Featured job functionality

\* Advanced recruiter features

\* No full AI analytics



\---



\### ENTERPRISE Plan



The Enterprise plan provides the complete recruiter feature set.



Features:



\* Unlimited job postings

\* Full AI interview access

\* Recruiter analytics

\* AI-powered analytics

\* Featured jobs

\* Advanced recruiter features



\---



\## 3. Feature Access Matrix



| Feature                     | FREE    | PRO          | ENTERPRISE  |

| --------------------------- | ------- | ------------ | ----------- |

| Job posting                 | Limited | Unlimited    | Unlimited   |

| AI interviews               | Limited | Higher limit | Full access |

| Recruiter analytics         | No      | Yes          | Yes         |

| AI analytics                | No      | No           | Yes         |

| Featured jobs               | No      | Yes          | Yes         |

| Advanced recruiter features | No      | Yes          | Yes         |



\---



\## 4. API Access Mapping



\### Job Creation API



Feature:



Create and publish jobs.



Subscription requirement:



\* FREE: Allowed until job posting limit is reached

\* PRO: Allowed without the Free-plan limit

\* ENTERPRISE: Allowed without the Free-plan limit



The API should verify that the employer has an active subscription before applying subscription-based restrictions.



\---



\### AI Interview APIs



Features:



\* Start AI interview

\* Generate AI interview questions

\* Submit AI answers

\* Evaluate AI answers



Subscription requirement:



\* FREE: Limited according to `ai\_interview\_limit`

\* PRO: Higher AI interview limit

\* ENTERPRISE: Full access



\---



\### Recruiter Analytics APIs



Features:



\* Recruiter analytics

\* Hiring statistics

\* Application analytics



Subscription requirement:



\* FREE: Not available

\* PRO: Available

\* ENTERPRISE: Available



\---



\### AI Analytics APIs



Features:



\* AI-powered recruiter analytics

\* AI-based hiring insights

\* Advanced AI evaluation analytics



Subscription requirement:



\* FREE: Not available

\* PRO: Not available

\* ENTERPRISE: Available



\---



\### Featured Job APIs



Feature:



Promote jobs as featured listings.



Subscription requirement:



\* FREE: Not available

\* PRO: Available

\* ENTERPRISE: Available



\---



\## 5. Subscription Validation Flow



The expected API access flow is:



Employer



↓



Check active subscription



↓



Identify subscription plan



↓



Check requested feature



↓



Check plan permissions and limits



↓



Allow or deny request



\---



\## 6. Subscription Status



Only an active subscription should provide paid feature access.



Supported subscription statuses:



\* ACTIVE

\* EXPIRED

\* CANCELLED

\* PENDING



Access rules:



\* ACTIVE → Subscription features available according to plan

\* EXPIRED → Paid features disabled

\* CANCELLED → Paid features disabled

\* PENDING → Paid features should not be treated as active



\---



\## 7. Payment Status



Payment transactions support the following states:



\* PENDING

\* SUCCESS

\* FAILED

\* REFUNDED



A successful payment can be associated with a subscription.



Failed, pending, or refunded transactions should not automatically grant paid feature access.



\---



\## 8. Access Control Summary



Subscription access is separate from authentication and authorization.



Authentication determines:



"Who is the user?"



Authorization determines:



"What is the user allowed to do?"



Subscription access determines:



"What paid features is the employer entitled to use?"



The three layers work together to protect subscription-based features.



\---



\## 9. Future Implementation



The current phase focuses on subscription and payment schema design and feature mapping.



Future implementation should add:



\* Subscription permission checks

\* Job posting limit enforcement

\* AI interview usage tracking

\* Payment gateway integration

\* Automatic subscription renewal

\* Subscription expiration handling

\* Invoice generation

\* Payment webhook processing

\* Subscription-related API permissions



\---



\## 10. Conclusion



The ZecPath subscription system provides a foundation for SaaS monetization.



The FREE, PRO, and ENTERPRISE plans define different levels of employer access.



Subscription status, payment status, feature permissions, and usage limits can be used together to control access to paid recruiter functionality.



