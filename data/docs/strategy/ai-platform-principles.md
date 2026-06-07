# AI Platform Principles

Managed AI platforms are preferred where governance, auditability, and integration with existing cloud controls are important. For internal enterprise workloads, the default recommendation is to use Amazon Bedrock or an approved managed platform unless a specific latency, sovereignty, model-control, or regulatory requirement justifies a custom-hosted model.

Teams should avoid building custom orchestration layers prematurely. The trade-off is operational control versus speed, safety, supportability, and cost. Start with the simplest governed option, prove value, then evolve the architecture.
