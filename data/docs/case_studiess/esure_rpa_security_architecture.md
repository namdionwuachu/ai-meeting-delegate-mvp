# esure_rpa_security_architecture.md

# Case Study: Secure RPA Platform for Regulatory Due Diligence

## Organisation

esure

## Domain

Insurance and Financial Services

## Challenge

The organisation was responsible for conducting due diligence and regulatory checks across a large number of third-party entities and suppliers.

The existing process was heavily manual and involved:

* Multiple systems
* Repetitive validation activities
* Significant operational effort
* Compliance risk
* Long processing times

The business wanted to automate the process while maintaining strict security and regulatory controls.

## Role

Senior Solution Architect

Responsible for:

* Solution architecture
* Security architecture
* AWS platform design
* Governance controls
* Stakeholder engagement
* Operational readiness

## Business Requirements

The solution needed to:

* Automate due diligence activities
* Reduce manual effort
* Meet regulatory obligations
* Protect sensitive information
* Operate within security policy constraints
* Support audit requirements

## Architecture

### Core Components

* AWS Virtual Private Cloud (VPC)
* Segregated security zones
* UiPath Unattended Robots
* AWS IAM
* CloudWatch
* AWS Systems Manager
* Secure storage services

### Security Model

The automation platform was deployed within a controlled environment using network segmentation and least-privilege access controls.

Key controls included:

* Segregated execution environment
* Role-based access control
* Encrypted communications
* Centralised logging
* Audit trail generation

### Operational Controls

Implemented:

* Robot monitoring
* Failure alerting
* Operational dashboards
* Recovery procedures
* Access reviews

## Key Architectural Decisions

### Unattended Robots

Selected because the process was highly repetitive and rules-based.

Benefits included:

* Reduced manual effort
* Consistent execution
* Improved throughput

### Security First Design

The platform was designed around regulatory and security requirements rather than automation requirements alone.

This prevented compliance becoming a blocker later in the programme.

### Network Segmentation

Robotic workloads operated within controlled network boundaries.

This reduced risk exposure and aligned with security governance requirements.

## Stakeholder Management

Worked closely with:

* Security teams
* Compliance teams
* Operational teams
* Business stakeholders

A significant portion of the project involved translating technical architecture decisions into business and regulatory outcomes.

## Results

* Significant reduction in manual processing effort
* Improved consistency of due diligence activities
* Enhanced auditability
* Reduced operational risk
* Improved regulatory compliance

## Lessons Learned

Automation projects often fail when security is treated as an afterthought.

Security architecture must be designed into the solution from the beginning.

## Leadership Reflection

The most difficult part of the programme was not the technology.

The challenge was aligning security, compliance, operations and business stakeholders behind a shared vision of success.

## Decision Pattern

When working in regulated industries:

1. Security requirements come first.
2. Compliance requirements are designed in rather than bolted on.
3. Automation should reduce risk as well as effort.
4. Governance is an accelerator, not a constraint.
