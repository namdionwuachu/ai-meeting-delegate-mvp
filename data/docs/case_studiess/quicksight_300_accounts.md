# quicksight_300_accounts.md

# Case Study: Multi-Account QuickSight Analytics Platform

## Organisation

Kaizen Reporting

## Domain

Cloud Cost and Operational Analytics

## Challenge

The organisation required a repeatable mechanism to deploy and manage Amazon QuickSight dashboards across more than 300 AWS accounts.

Challenges included:

* Dashboard consistency
* Cross-account deployment
* Data sovereignty requirements
* Operational overhead
* User adoption

Traditional manual deployment approaches were not scalable.

## Role

Lead Solution Architect

Responsible for:

* Solution architecture
* Multi-account design
* Automation strategy
* Governance model
* Deployment framework

## Architecture

### Core Components

* Amazon QuickSight
* AWS Lambda
* Asset Bundles
* CloudFormation
* Amazon Athena
* Amazon S3
* SNS Notifications

### Deployment Model

Created a centralised publishing framework capable of:

* Exporting dashboard assets
* Deploying templates
* Creating datasets
* Publishing dashboards
* Managing permissions

### Governance

Implemented:

* Account-level segregation
* Standardised dashboard templates
* Controlled deployment workflows
* Audit logging

## Key Architectural Decisions

### Asset Bundles over Manual Recreation

Asset Bundles allowed:

* Consistency
* Repeatability
* Version control
* Reduced operational effort

### Central Publishing Model

A single deployment framework reduced support overhead and increased standardisation.

## Results

* Successfully supported 300+ AWS accounts
* Achieved approximately 95% adoption
* Reduced dashboard deployment effort dramatically
* Improved governance and consistency

## Lessons Learned

Analytics platforms succeed when deployment and governance are treated as first-class architectural concerns.

## Decision Pattern

Standardise once and automate everywhere.
