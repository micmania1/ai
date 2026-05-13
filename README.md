# AI

A personal collection of AI skills, agents, and tools for enhancing development workflows.

## Skills

### `/ui`

``` 
npx skills add https://github.com/micmania1/ai --skill ui
```

What it does: `/ui` builds a temporary custom user interface that integrates with your Claude Code session. It offers interactable information in a presentable way that fits the context of your problem.

**Example #1:**

> /ui generate a list of coding practices then build a tabular interface with an accept & deny buttons. Record each decision in my project development guidelines. 

In this example, instead of trawling through a large list of text, have it presented in a easier to digest format with buttons which push your decision back to Claude Code.

**Example #2** 

> /ui build a game of tic-tac-toe so I can play you. Your move first.

In this example we could try and play an ascii game of naughts and crosses and describe where you want to take your turn, or you could have a purpose built ui which feeds your selection back into your Claude Code session.


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
