\# ZecPath Payment and Subscription Schema Design



\## 1. Overview



The ZecPath backend uses four models to support SaaS subscriptions and payment tracking:



\* SubscriptionPlan

\* UserSubscription

\* PaymentTransaction

\* BillingHistory



These models provide the database foundation for subscription management, payment tracking, and billing records.



\---



\## 2. SubscriptionPlan



The `SubscriptionPlan` model defines the available SaaS plans.



Supported plans:



\* FREE

\* PRO

\* ENTERPRISE



Important fields include:



\* `name`

\* `description`

\* `price`

\* `currency`

\* `billing\_cycle`

\* `job\_post\_limit`

\* `ai\_interview\_limit`

\* `analytics\_enabled`

\* `ai\_analytics\_enabled`

\* `is\_active`

\* `created\_at`

\* `updated\_at`



The model defines what features and limits are available for each subscription plan.



\---



\## 3. UserSubscription



The `UserSubscription` model represents an employer's subscription.



It connects:



Employer → SubscriptionPlan



Important fields include:



\* `employer`

\* `plan`

\* `status`

\* `started\_at`

\* `expires\_at`

\* `auto\_renew`

\* `created\_at`

\* `updated\_at`



Supported subscription statuses:



\* ACTIVE

\* EXPIRED

\* CANCELLED

\* PENDING



This model determines the employer's current subscription state.



\---



\## 4. PaymentTransaction



The `PaymentTransaction` model records individual payment transactions.



It connects:



Employer → PaymentTransaction → UserSubscription



Important fields include:



\* `employer`

\* `subscription`

\* `amount`

\* `currency`

\* `transaction\_id`

\* `payment\_method`

\* `status`

\* `paid\_at`

\* `created\_at`



Supported payment statuses:



\* PENDING

\* SUCCESS

\* FAILED

\* REFUNDED



The unique `transaction\_id` provides a unique reference for each payment.



\---



\## 5. BillingHistory



The `BillingHistory` model stores billing and invoice information.



It connects:



Employer → BillingHistory



and can reference:



\* UserSubscription

\* PaymentTransaction



Important fields include:



\* `employer`

\* `subscription`

\* `transaction`

\* `amount`

\* `currency`

\* `billing\_period\_start`

\* `billing\_period\_end`

\* `invoice\_number`

\* `status`

\* `created\_at`



Supported billing statuses:



\* PAID

\* PENDING

\* FAILED

\* REFUNDED



The unique `invoice\_number` provides a unique billing record reference.



\---



\## 6. Relationship Design



The overall relationship is:



Employer



↓



UserSubscription



↓



SubscriptionPlan



and:



Employer



↓



PaymentTransaction



↓



UserSubscription



and:



Employer



↓



BillingHistory



├── UserSubscription



└── PaymentTransaction



\---



\## 7. Payment Lifecycle



The expected payment lifecycle is:



Subscription selected



↓



Payment created



↓



Payment pending



↓



Payment gateway processing



↓



Payment successful



↓



Subscription activated



↓



Billing record created



If payment fails:



Payment failed



↓



Subscription remains inactive



If a payment is refunded:



Payment refunded



↓



Subscription access is handled according to the refund policy.



\---



\## 8. Subscription Lifecycle



The subscription lifecycle is:



PENDING



↓



ACTIVE



↓



EXPIRED



or



ACTIVE



↓



CANCELLED



The subscription should only provide paid feature access while its status is ACTIVE and its validity period permits access.



\---



\## 9. Current Phase



The current implementation provides the database schema required for subscription and payment management.



Actual payment gateway integration is outside the current schema-design phase.



Future payment integration may include:



\* Payment gateway

\* Payment webhooks

\* Automatic renewal

\* Refund processing

\* Invoice generation

\* Payment verification



\---



\## 10. Conclusion



The four-model subscription and payment architecture provides the foundation required for ZecPath SaaS monetization.



Subscription plans define available features and limits.



User subscriptions determine employer access.



Payment transactions record financial events.



Billing history provides a persistent record of invoices and billing periods.



