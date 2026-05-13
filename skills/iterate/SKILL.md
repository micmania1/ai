---
name: iterate
description: >-
  Iterate through a problem to relentlessly find loose threads and tie off the loose ends
user-invocable: true
---

# Iterate

As an AI Agent, you will orchestrate a subagent to seek an answer for the user prompt. 

Take the answer from the subagent and pass it into another subagent in the following format:

```
Your task is to iterately find authentic, grounded answers to the following query: {query}

This is research already done:
{previous_subagent_answer}

Find any information related to the query and add it to the existing research. 

If you cannot find any more information, respond with the previous answer and respond telling me you can't find anything more.
```

You will keep iterating through this process, passing one answer to the next subagent until there is no more information to find.

However, every 20 iterations, you MUST ask the user if they would like to continue or use the answers found so far.