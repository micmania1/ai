# AI

A personal collection of AI skills, agents, and tools for enhancing development workflows.

## Skills

### `/refine`

```
npx skills add https://github.com/micmania1/ai --skill refine
```

What is does: `/refine` will refine an issue, story or bug, then virtually step through the codebase to find gaps in requirements.

This skill is based on the `/grill-me`skill by Mat Pocock but aims to limit the session to critical requirements only.

**Example #1:** 

> /iterate #99

This example would refine a Github issue with the id of 99. Alt: `/refine https://github.com/acme/proj/issues/99`



**Example #2:** 

> /iterate XYZ-123

This example would refine a Jira story. You may also pass the full URL. eg. `https://<org>.atlassian.net/browser/XYZ-123`


### `/iterate`

```
npx skills add https://github.com/micmania1/ai --skill iterate
```

What is does: `/iterate` attempts to thoroughly investigate and adress user queries by looping through subagents, pushing them to find more information until new information is exhausted.

**Example #1:** 

> /iterate fully map out the sign up process for my application and which systems it touches. 

**Example #2:**

> /iterate review my @solution-design.md and prepare a list of questions where you find logical gaps, inconsistencies or serious ambiguity. When you're done, interview me using the questions.

`/iterate` is a low-level skill that may be used in combination with other skills or by subagents to complete routines.


## Experimental Skills

### `/ui`

```
npx skills add https://github.com/micmania1/ai --skill ui
```

What it does: `/ui` builds a temporary custom user interface that integrates with your Claude Code session. It offers interactable information in a presentable way that fits the context of your problem.

**Experimental Findings**
This skill experiements with the concept of generative UI to help solve a problem instead of being limited to chat and walls of text. After trying to find use-cases for this, I think its best to use this approach with purpose built UIs for specific tasks. An example fo this concept out in the wild now is impeccable where they've created a chrome plugin which overlays UI on an existing web page and has claude monitor for events.

**Example #1:**

> /ui generate a list of coding practices then build a tabular interface with an accept & deny buttons. Record each decision in my project development guidelines. 

In this example, instead of trawling through a large list of text, have it presented in a easier to digest format with buttons which push your decision back to Claude Code.

**Example #2** 

> /ui build a game of tic-tac-toe so I can play you. Your move first.

In this example we could try and play an ascii game of naughts and crosses and describe where you want to take your turn, or you could have a purpose built ui which feeds your selection back into your Claude Code session.



