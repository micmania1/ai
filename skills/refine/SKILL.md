---
name: refine
description: >-
  Refine a story or bug. Rewrites the description with a simple user-story format.
user-invocable: true
---

<USER_INPUT>
$ARGUMENTS[input]
</USER_INPUT>

Review the USER_INPUT and classify it as a story or a bug.

Interrogate the input relentlessly until you have a full understanding of what it takes to build the feature, virtually stepping through the development without changing any code.

Then I want you to find critical gaps that have been missed or identify critical discrepancies in the story against the design, or existing codebase and clarify the intent.

Interview me one question at a time showing a count (eg. 1 of N). Always start the interview by reinforcing the intent of the user input in a single sentence.

A story should match the following template:

```
## Story

**Given** I am a <persona / context>
**When** I <do the thing>
**Then** I should <see / be able to>
**So that** <user value>

## Functional Requirements

- <Short, self-contained, testable statement of user-visible behaviour.>

## Out of scope

- <item> — <short one-line reason, link sibling story if applicable>

## Design
<Optional section. Include only if the story has UI elements.>
<Include any URLs to resources such as figma and include the node ids etc.>
<Otherwise, describe what should be achieved. You may use ascii to record layout concepts.>


<Any other topic can be listed below with a title and content>
```


A bug should match the following template:

```
## Bug
<Short description of the bug and its impact>

## Steps to Reproduce
<Steps to reproduce the behaviour>

## Expected Behaviour
<Where the steps to reprduce eplain the wrong behaviour, this should describe what should happen instead>

<Any other topic can be listed below with a title and content>
```

