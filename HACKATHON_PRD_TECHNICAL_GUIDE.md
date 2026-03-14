# Technical Documentation: How `HACKATHON_PRD.md` Must Be Written

Version: `v1.0`
Status: `Authoring Guide`
Last Updated: `2026-03-14`

## 1. Purpose

This document defines the technical standard for creating and maintaining [`HACKATHON_PRD.md`](/Users/aroraji/vivriti/HACKATHON_PRD.md).

`HACKATHON_PRD.md` is the product requirements document for the hackathon build. It is not a marketing note, not a pitch deck, and not an architecture-only document. It must function as the single product-definition reference that the team can use to:

- understand what is being built
- align implementation with the hackathon brief
- scope the MVP correctly
- trace product decisions back to hackathon requirements
- guide engineering, design, and demo preparation

## 2. Document Objective

The PRD must answer five questions precisely:

1. What problem are we solving?
2. What exactly are we building for the hackathon?
3. What must the user be able to do end to end?
4. What is in scope versus out of scope?
5. How will we know the solution satisfies the hackathon?

If the document does not make those five things unambiguous, it is incomplete.

## 3. Role of the PRD in the Project

`HACKATHON_PRD.md` must sit above implementation details and below the hackathon problem statement.

It should translate the challenge into a buildable product definition.

### It must do

- define product scope
- define user journey
- define mandatory functionality
- define success criteria
- define constraints and assumptions
- define MVP boundaries
- define acceptance criteria

### It must not do

- replace detailed API documentation
- replace database schema specs
- replace frontend wireframes
- replace runbooks or deployment docs
- include low-level code decisions unless they materially affect scope

## 4. Source Inputs the PRD Must Be Based On

The PRD must be derived from the following inputs:

- the hackathon problem statement
- the hosted-application user journey requirement
- the list of five mandatory document categories
- the three required solution pillars
- the judging criteria
- India-specific lending context
- actual project constraints such as time, hosting, data quality, and demo expectations

No feature should be added to the PRD unless it can be justified by at least one of:

- hackathon requirement
- user workflow necessity
- demo necessity
- explainability necessity

## 5. Writing Standard

The PRD must be written as an execution document.

### Tone

- direct
- concrete
- implementation-aware
- non-promotional
- unambiguous

### Style Rules

- use short sections with clear headers
- prefer bullets over long prose for requirements
- separate goals, scope, requirements, and acceptance criteria
- avoid vague words like “smart”, “powerful”, “robust” unless they are operationally defined
- if a requirement can be tested, write it so it is testable

### Language Rules

- use “must” for mandatory requirements
- use “should” for preferred but non-blocking requirements
- use “may” for optional capabilities
- avoid mixing product intent with technical implementation unless needed for clarity

## 6. Structural Contract for `HACKATHON_PRD.md`

The PRD must contain the following categories of sections.

### 6.1 Executive Layer

This layer establishes what the product is.

Mandatory content:

- product name
- one-line pitch
- hackathon goal
- why this product matters

Purpose:

- orient any reader in under one minute

### 6.2 Problem Layer

This layer explains the operational pain in credit appraisal.

Mandatory content:

- current workflow pain
- data fragmentation
- speed and latency problem
- bias and missed-signal problem
- Indian lending context

Purpose:

- justify why the product exists

### 6.3 Vision and Goals Layer

This layer defines product direction.

Mandatory content:

- product vision
- primary goals
- secondary goals
- explicit non-goals

Purpose:

- stop scope drift
- keep the build aligned with the hackathon

### 6.4 User Layer

This layer defines users and their responsibilities.

Mandatory content:

- primary user persona
- secondary reviewer persona
- optional tertiary operator persona
- user pain points
- what each persona needs from the app

Purpose:

- keep the workflow user-driven instead of model-driven

### 6.5 Hackathon Mapping Layer

This layer is mandatory and must explicitly map the product to the challenge.

Mandatory content:

- mapping to the 3 pillars:
  - data ingestor
  - research agent
  - recommendation engine
- mapping to the 4 hosted user stages
- mention of the required five uploaded document types
- mapping to judging criteria

Purpose:

- make it obvious to the team and judges that the product directly answers the brief

### 6.6 Scope Layer

This layer defines what is being built now.

Mandatory content:

- MVP scope
- mandatory features
- nice-to-have features
- deferred features

Purpose:

- ensure the build is shippable within hackathon time

### 6.7 Functional Requirements Layer

This is the core of the PRD.

Mandatory content:

- stage-wise requirements
- input and output expectations
- review and correction flows
- report generation requirements
- explainability requirements

This layer must be organized by workflow stage:

1. onboarding
2. ingestion
3. extraction and schema mapping
4. research, analysis, and reporting

Purpose:

- define exactly what the system must let the user do

### 6.8 Recommendation Layer

This layer defines decisioning behavior.

Mandatory content:

- recommendation outputs
- explainability expectations
- structure of scoring logic
- policy and risk logic boundaries

Purpose:

- prevent the decision engine from becoming a vague black box

### 6.9 India-Specific Logic Layer

This section is mandatory for this hackathon.

Mandatory content:

- GST-related checks
- turnover mismatch logic
- circular trading or revenue inflation heuristics
- promoter or shareholding interpretation
- India-relevant regulatory and litigation sensitivity

Purpose:

- satisfy the “Indian context sensitivity” judging criterion

### 6.10 Research Layer

This section defines how external intelligence is used.

Mandatory content:

- research targets
- research categories
- evidence structure
- research output model
- source visibility expectations

Purpose:

- make research a first-class product capability, not a side feature

### 6.11 CAM / Report Layer

This section defines the final deliverable.

Mandatory content:

- required report sections
- report format expectations
- recommendation presentation
- evidence and confidence expectations

Purpose:

- ensure the final output is demo-ready and lender-like

### 6.12 UX Layer

This section defines the user journey quality.

Mandatory content:

- UX principles
- critical screens
- progress visibility
- demo clarity expectations

Purpose:

- force product-level UX discipline early

### 6.13 Architecture / Data Layer

This section should stay high-level and product-relevant.

Mandatory content:

- major system components
- data flow abstraction
- core domain objects
- compatibility with Databricks-oriented ingestion concept

Purpose:

- align engineering without overloading the PRD with implementation detail

### 6.14 Non-Functional Requirements Layer

Mandatory content:

- hosting expectations
- performance expectations
- reliability expectations
- auditability
- security basics

Purpose:

- capture deployment and operational constraints from the hackathon

### 6.15 Delivery Layer

Mandatory content:

- prioritization
- risks
- mitigations
- acceptance criteria
- demo narrative

Purpose:

- connect the PRD to execution and evaluation

## 7. Requirement Quality Rules

Every requirement in `HACKATHON_PRD.md` must satisfy these rules.

### Rule 1: It must be observable

Bad:

- “the system should be intelligent”

Good:

- “the system must fetch and display secondary research findings with source URL, category, date, and summary”

### Rule 2: It must map to user or judge value

Bad:

- “use cutting-edge models”

Good:

- “allow the analyst to review and edit auto-classified document labels before extraction proceeds”

### Rule 3: It must avoid hidden assumptions

If the requirement depends on:

- data availability
- human review
- external APIs
- hosting limitations

that dependency must be stated explicitly.

### Rule 4: It must distinguish mandatory from optional

Use:

- mandatory MVP
- nice-to-have
- post-hackathon

not one undifferentiated feature list.

### Rule 5: It must be hackathon-realistic

The PRD must not require:

- dozens of external integrations
- enterprise-grade infra not needed for the demo
- opaque ML pipelines that cannot be explained live

## 8. Section-by-Section Technical Expectations

This section defines what “done” means for each major PRD section.

### Executive Summary

Done when:

- a new reader can understand the product in less than one minute

### Problem Statement

Done when:

- it clearly explains why current corporate credit underwriting is slow and fragmented

### Personas

Done when:

- the team can identify whose workflow each feature serves

### Hackathon Alignment

Done when:

- all three pillars and all four stages are explicitly reflected

### Functional Requirements

Done when:

- a designer or engineer can infer the main screens and service boundaries

### Recommendation Engine

Done when:

- the output decision structure is explicit and explainability is first-class

### CAM Section

Done when:

- the structure of the final downloadable report is unambiguous

### Acceptance Criteria

Done when:

- the team can objectively decide whether the product is ready for demo

## 9. Traceability Rules

Each major PRD section should be traceable to one or more of:

- hackathon requirement
- user need
- evaluation criterion
- deployment constraint

If a feature cannot be traced to one of these, it should be questioned.

### Recommended Traceability Approach

For each large feature area, the team should be able to answer:

- which hackathon pillar does this serve?
- which stage of the user journey does this belong to?
- which judging criterion does this improve?

## 10. Technical Boundaries of the PRD

The PRD should define system behavior, not full technical implementation.

### Appropriate technical detail in PRD

- key system components
- data object concepts
- high-level orchestration
- explainability and evidence expectations
- deployment constraints

### Inappropriate technical detail in PRD

- full REST endpoint inventory
- complete DB DDL
- exact class hierarchy
- line-by-line pipeline logic
- framework-specific internal abstractions

Those belong in separate technical design documents.

## 11. Maintenance Rules

`HACKATHON_PRD.md` must be treated as a live product contract during the hackathon.

### When it must be updated

- scope changes
- stage changes
- added or dropped mandatory features
- major scoring or explainability changes
- report structure changes
- deployment constraints change

### When it should not be updated

- minor implementation detail changes that do not affect product behavior
- low-level refactors
- code-only naming changes

### Change Management Rules

- keep the version/date updated
- do not silently remove required hackathon flows
- if scope is reduced, mark what was deferred
- do not let the PRD and demo narrative diverge

## 12. Review Checklist for `HACKATHON_PRD.md`

Before considering the PRD final, verify:

- it clearly states the product and hackathon goal
- it maps directly to the 3 pillars
- it maps directly to the 4 user stages
- it includes all 5 required document categories
- it includes analyst-in-the-loop correction
- it includes secondary research
- it includes primary due diligence note integration
- it includes explainable recommendation logic
- it includes CAM/report generation
- it includes hosted deployment expectations
- it includes India-specific underwriting logic
- it distinguishes MVP from later work
- it includes acceptance criteria
- it is readable under time pressure

## 13. Definition of a Good PRD for This Hackathon

For this project, a good `HACKATHON_PRD.md` is one that:

- is directly aligned with the brief
- is detailed enough to execute against
- is narrow enough to finish
- is concrete enough to review against
- is clear enough to use in a live demo narrative

If the document sounds impressive but does not help the team decide what to build next, it is not good enough.

## 14. Recommended Follow-On Documents

After the PRD, the team should create:

- implementation plan
- system design / architecture spec
- API contract
- data model specification
- evaluation and demo script
- deployment checklist

These should derive from the PRD, not contradict it.

## 15. Final Rule

`HACKATHON_PRD.md` must define the product in a way that makes the rest of the build obvious.

If engineering, design, and demo prep still need to guess the intended workflow after reading it, the PRD is not finished.
