\# Test Cases



\## Test Summary



The Customer Support Chatbot was validated using functional and end-to-end test scenarios covering intent classification, routing, bug-report formatting, Lambda execution, and DynamoDB persistence.



| ID | Test Case | Expected Result | Actual Result | Status |

|---|---|---|---|---|

| TC-01 | Complete bug report | Routed to Bug Report path and persisted in DynamoDB | Ticket created successfully and persisted | PASS |

| TC-02 | Incomplete bug report | Missing information is not invented; optional fields remain empty | Ticket created with missing fields empty | PASS |

| TC-03 | Platform question | Routed to FAQ / Platform Question path | Correctly routed without creating a ticket | PASS |

| TC-04 | Other request | Routed to Human Support path | Correctly routed | PASS |

| TC-05 | Realistic checkout bug | Routed through Formatter → Lambda → DynamoDB | Ticket created and persisted successfully | PASS |



\*\*Overall Result: 5/5 tests passed.\*\*



\---



\## TC-01 — Complete Bug Report



\### Input



```text

The checkout page crashes when I click Pay Now.

Steps: Open checkout, add an item, and click Pay Now.

Environment: Chrome on Windows.

