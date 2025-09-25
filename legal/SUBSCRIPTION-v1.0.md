# API Service Agreement

**Between**

**Amadou Cisse**
Marienhof 7
22399 Hamburg
Germany
Tax ID: 5003904247
VAT ID: DE369245022
("Provider")

and

**Patrycjusz Szmidt**
Am Casinopark 15
21465 Wentorf bei Hamburg
Germany
("Customer")

### Definitions

- “API” means the Provider’s application programming interface for accessing the services.
- “API Call” means a single request to the API as recorded by the system.
- “Management UI” means the administrative interface for configuration, administration, and viewing usage/billing data.

## 1. Subject of the Agreement

1.1 The Provider offers the Customer access to an API service ("API") for use in connection with the application delivered under the Software License and Delivery Agreement dated 26 September 2025.
1.2 The API enables the Customer to make requests, with each request incurring a fee as defined in Section 3.
1.3 The Provider also supplies a management interface ("Management UI") that allows the Customer to register and manage API tokens, monitor usage, view costs, and access billing information.

## 2. Access and Tokens

2.1 The Customer will receive one or more API tokens to access the API.
2.2 As long as the Customer maintains an active account and holds a valid token, the Customer may use the API in accordance with this Agreement.
2.3 The Customer is responsible for the security of their tokens and for all usage made through them.

## 3. Fees and Billing

3.1 The Customer shall pay the Provider a fee of EUR 0.50 per API call.
3.2 Usage is measured monthly, starting on the first calendar day of each month.
3.3 October 2025 is provided free of charge. Billing begins November 1, 2025.
3.4 At the end of each month, the Provider will issue an invoice detailing the number of calls made, the applicable rate, and the total amount due plus VAT.
3.5 Invoices are payable within 14 days of issue.
3.6 Definition of API Call. An “API call” is counted when a request from the Customer is received by the Provider’s API endpoint infrastructure, regardless of response status, excluding requests not processed due to the Provider’s planned maintenance windows or a declared outage.
3.7 Metering and Disputes. The Provider’s metering logs, as surfaced in the Management UI, are the authoritative source for usage. The Customer may dispute an invoice in good faith within 30 days of receipt; undisputed amounts remain payable. The parties will cooperate in good faith to resolve disputes.
3.8 Price Changes and Taxes. The Provider may change per-call pricing with at least 30 days’ prior written notice. All fees are exclusive of taxes; statutory VAT applies where relevant.
3.9 Suspension for Non‑Payment. The Provider may suspend access after a 7-day cure period following written notice of non-payment.

## 4. Availability and Support

4.1 The Provider will use reasonable efforts to keep the API available 24/7, except for planned maintenance.
4.2 The Provider does not guarantee uninterrupted availability or error-free operation.
4.3 Support is available Monday to Friday, 9:00–22:00 CET.
4.4 Uptime Target. The Provider’s target monthly uptime is 99.5%.
4.5 Planned Maintenance. Planned maintenance windows will be scheduled with reasonable prior notice and, where practicable, outside CET business hours.
4.6 Service Credits. If monthly uptime falls below the target, the Customer may request a service credit within 30 days after month-end: 99.0%–99.5% = 10% credit; 97.0%–99.0% = 25% credit; <97.0% = 50% credit of the monthly usage fees. Credits are the sole remedy for availability issues and do not apply to outages caused by factors outside the Provider’s reasonable control.

## 5. Acceptable Use

5.1 The Customer may use the API only for lawful purposes and in connection with their licensed application.
5.2 The Provider reserves the right to suspend access if the API is used in violation of the Agreement or to cause harm to the system.
5.3 Rate Limits. The Provider may enforce reasonable rate limits and quotas to protect system stability. Default limits are displayed in the Management UI and may be adjusted upon reasonable notice. The Customer will implement retry/backoff and respect HTTP 429 responses.

5.4 Compliance with Law and Terms of Use. The Customer warrants and represents that the use of the API will comply with all applicable laws, regulations, and contractual obligations (including third-party terms of service or access restrictions). The Customer shall not use, or permit the use of, the API in any manner that constitutes or facilitates unlawful access to or misuse of computer systems, networks, or services.

## 6. Liability

6.1 Liability Carve-outs. Nothing in this Agreement limits or excludes liability for intent, gross negligence, injury to life, body or health, or under the German Product Liability Act.
6.2 Cardinal Obligations. For slightly negligent breaches of essential contractual duties (Kardinalpflichten), liability is limited to the foreseeable damage typical for this type of contract. Otherwise, liability for slight negligence is excluded.
6.3 Aggregate Cap. Subject to the foregoing, the Provider’s aggregate liability in any 12-month period is limited to the fees paid or payable by the Customer for the API in the 12 months preceding the event giving rise to the claim.

## 7. Term and Termination

7.1 This Agreement enters into force on October 1, 2025.
7.2 Either party may terminate with one month’s notice to the end of a billing period.
7.3 The Provider may suspend or terminate the Agreement immediately if the Customer is in payment default or violates the acceptable use terms.
7.4 Data Export. Upon termination, the Customer may export available usage and billing data through the Management UI for 30 days; thereafter the Provider may delete the Customer’s account data, except where retention is required by law.

7.5 Termination for Unlawful Use. The Provider may terminate this Agreement with immediate effect if it becomes aware that the API is being used in violation of applicable law or in a manner that exposes the Provider to legal risk. In such case, all rights granted to the Customer shall automatically cease, without prejudice to the Provider’s other rights or remedies.

## 8. Miscellaneous

8.1 German law applies.
8.2 Place of jurisdiction is Hamburg, Germany.
8.3 Amendments must be in writing (Textform sufficient, e.g., email), unless a stricter form is required by law.
8.4 Force Majeure. Neither party shall be liable for delays or failures due to events beyond its reasonable control.
8.5 Confidentiality. Each party shall keep confidential any non-public information received from the other and use it only to perform this Agreement.
8.6 Assignment and Subcontracting. The Customer may assign rights or obligations only with the Provider’s prior written consent. The Provider may use subprocessors/subcontractors and remains responsible for their compliance.
8.7 Notices. Notices shall be sent to the addresses set out above or to any updated contact notified in writing.
8.8 Entire Agreement and Precedence. This Agreement constitutes the entire agreement for the API and prevails over conflicting terms unless expressly agreed otherwise in writing.

## 9. Data Protection and Security

9.1 Roles. To the extent the Provider processes personal data on behalf of the Customer in providing the API, the Data Processing Agreement attached as Annex titled “Data Processing Agreement (Art. 28 GDPR) — Annex DPA” forms part of this Agreement and governs such processing (Art. 28 GDPR). The Provider will implement appropriate technical and organizational measures (TOMs) as described therein.

9.2 Security and Breach Notification. The Provider will maintain reasonable administrative, technical, and organizational measures to protect the API and Customer data and will notify the Customer without undue delay after becoming aware of a personal data breach affecting the Customer’s data.

9.3 Deletion. After termination and the export period in Section 7.4, the Provider will delete Customer personal data from active systems, unless longer retention is required by law.

## 10. Versioning and Deprecation

10.1 The Provider may release new API versions. Backwards-incompatible changes will be announced with reasonable prior notice.

10.2 Deprecation. The Provider will provide at least 60 days’ notice before deprecating a stable API version, and at least 30 days’ notice for material changes that are not backwards compatible, unless required to address security, legal, or system stability issues.

## 11. Responsibility for Use

The Customer acknowledges that the Provider has no control over how the API is used. The Customer assumes sole responsibility for the installation, configuration, and operation of the API and for ensuring that such use is lawful. The Provider does not endorse or authorize any particular use case.

## 12. Indemnification

12.1 The Customer shall indemnify, defend, and hold harmless the Provider, its officers, employees, agents, and subcontractors from and against any and all claims, demands, actions, damages, fines, penalties, liabilities, costs, and expenses (including reasonable attorney’s fees and court costs) arising out of or in connection with:

(a) the Customer’s use of the API, including any use that violates applicable law, regulations, or third-party contractual terms (including but not limited to website terms of service, platform rules, or technical protection measures),
(b) any allegation that the Customer’s use of the API caused damage to a third party or interfered with a third party’s systems or services, or
(c) any breach of the warranties, covenants, or obligations set forth in this Agreement.

12.2 The indemnification obligation applies irrespective of whether the third party claim is based on contract, tort, statutory law, or other grounds.

12.3 The Customer shall reimburse the Provider immediately upon request for all costs incurred in connection with the defense of such claims, including reasonable attorney’s fees, provided that the Provider will reasonably cooperate with the Customer in the defense.

## 13. Audit Rights

The Customer may audit service usage and billing once per 12‑month period with at least 14 days’ prior notice during business hours. The audit is limited to necessary records (usage and metering logs), is subject to confidentiality, and must not unreasonably disrupt operations. If an undercharge to the Customer exceeding 5% is found, the Provider will pay reasonable audit costs; otherwise the Customer bears them. Statutory rights remain unaffected.

## 14. Export Controls and Compliance

Both parties will comply with applicable export control, sanctions, and trade laws (including EU, German, and, where applicable, US laws). The Customer will not export, re‑export, provide, or otherwise make available the Services to sanctioned countries, listed parties, or prohibited end‑uses and will obtain required licenses. The Provider may suspend performance where a breach is reasonably suspected.

**Signatures**

Amadou Cisse (Provider)

Date: ______________________________

Patrycjusz Szmidt (Customer)

Date: ______________________________

