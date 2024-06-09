{{role_desc}}
Your goal 

{% for tool in tools%}
{{tool[0]}}: {{tool[1]}}
{% endfor %}

To use a tool, you MUST use exactly the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{% for tool in tools%}{{tool[0]}}, {% endfor %}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
AI: [your response here]
```

Do NOT output in any other format. Begin!

New input: {{input}}
{{agent_scratchpad}}