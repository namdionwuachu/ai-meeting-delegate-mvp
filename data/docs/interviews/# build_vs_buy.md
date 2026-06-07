# build_vs_buy.md

# Build vs Buy

## Question

Should we build or buy a platform or capability?

## Namdi's View

My view is that organisations should default to managed services and commercial platforms unless there is a compelling business reason to build.

The trade-off here is flexibility versus operational overhead.

Building provides greater control but introduces platform ownership, maintenance, security responsibilities, operational support, and technical debt.

Buying accelerates time to value and benefits from vendor investment, support, and feature evolution.

## Decision Framework

Evaluate:

* Business differentiation
* Time to market
* Total cost of ownership
* Operational complexity
* Internal capability
* Security and compliance requirements

## Recommendation

Start with managed services and evolve towards custom capabilities only where differentiation creates measurable business value.

---

# ecs_vs_eks.md

# ECS vs EKS

## Question

When should ECS be used instead of EKS?

## Namdi's View

My view is that ECS should be the default choice for most organisations.

The trade-off here is simplicity versus flexibility.

ECS offers:

* Lower operational overhead
* Faster onboarding
* Native AWS integration
* Simpler security model

EKS becomes attractive when:

* Kubernetes skills already exist
* Multi-cloud portability is required
* Standardisation on Kubernetes is a strategic objective

## Recommendation

Default to ECS unless there is a clear requirement for Kubernetes.
