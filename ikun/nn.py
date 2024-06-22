from ikun.core import *
from ikun.nb_env import ExecuteNbCode

INTERPRETER_SYSTEM_MSG = """As a data scientist, you need to help user to achieve their goal step by step in a continuous Jupyter notebook. 
Since it is a notebook environment, don't use asyncio.run. Instead, use await if you need to call an async function."""

STRUCTURAL_PROMPT = """
# User Requirement
{user_requirement}

# Plan Status
{plan_status}

# Tool Info
{tool_info}

# Constraints
- Take on Current Task if it is in Plan Status, otherwise, tackle User Requirement directly.
- Ensure the output new code is executable in the same Jupyter notebook as the previous executed code.
- Always prioritize using pre-defined tools for the same functionality.

# Output
While some concise thoughts are helpful, code is absolutely required. Always output one and only one code block in your response. Output code in the following format:
```python
your code
```
"""

REFLECTION_SYSTEM_MSG = """You are an AI Python assistant. You will be given your previous implementation code of a task, runtime error results, and a hint to change the implementation appropriately. Write your full implementation."""

DEBUG_REFLECTION_EXAMPLE = '''
[previous impl]:
assistant:
```python
def add(a: int, b: int) -> int:
   """
   Given integers a and b, return the total value of a and b.
   """
   return a - b
```

user:
Tests failed:
assert add(1, 2) == 3 # output: -1
assert add(1, 3) == 4 # output: -2

[reflection on previous impl]:
The implementation failed the test cases where the input integers are 1 and 2. The issue arises because the code does not add the two integers together, but instead subtracts the second integer from the first. To fix this issue, we should change the operator from `-` to `+` in the return statement. This will ensure that the function returns the correct output for the given input.

[improved impl]:
def add(a: int, b: int) -> int:
   """
   Given integers a and b, return the total value of a and b.
   """
   return a + b
'''

REFLECTION_PROMPT = """
[example]
Here is an example of debugging with reflection.
{{debug_example}}
[/example]

[context]
{{context}}

[previous impl]:
{{previous_impl}}

[instruction]
Analyze your previous code and error in [context] step by step, provide me with improved method and code. Remember to follow [context] requirement. Don't forget to write code for steps behind the error step.
Output following the format:
reflection:
Reflection on previous implementation.
improved_impl:
```python
Refined code after reflection.
```
"""

CHECK_DATA_PROMPT = """
# Background
Check latest data info to guide subsequent tasks.

## Finished Tasks
```python
{code_written}
```end

# Task
Check code in finished tasks, print key variables to guide your following actions.
Specifically, if it is a data analysis or machine learning task, print the the latest column information using the following code, with DataFrame variable from 'Finished Tasks' in place of df:
```python
from metagpt.tools.libs.data_preprocess import get_column_info

column_info = get_column_info(df)
print("column_info")
print(column_info)
```end
Otherwise, print out any key variables you see fit. Return an empty string if you think there is no important data to check.

# Constraints:
- Your code is to be added to a new cell in jupyter.

# Instruction
Output code following the format:
```python
your code
```
"""

DATA_INFO = """
# Latest Data Info
Latest data info after previous tasks:
{info}
"""


class DebugWithReflection(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt = JJPrompt(REFLECTION_PROMPT, sys_prompt=REFLECTION_SYSTEM_MSG,
                               debug_example=DEBUG_REFLECTION_EXAMPLE)
        self.llm = OpenAIBackend(model="gpt-3.5-turbo")

    async def forward(self, x):
        prompt = await self.prompt(x)
        return await self.llm(prompt)


class WriteAnalysisCode(Action):
    def __init__(self, user_requirement, plan_status, tool_info, use_reflection=False, **kwargs):
        self.use_reflection = use_reflection
        self.prompt = JJPrompt(
            STRUCTURAL_PROMPT,
            INTERPRETER_SYSTEM_MSG,
            user_requirement=user_requirement,
            plan_status=plan_status,
            tool_info=tool_info
        )
        self.llm = OpenAIBackend(model="gpt-3.5-turbo")
        self.debug = DebugWithReflection()
        super().__init__(**kwargs)

    async def forward(self, x):
        working_memory = x["working_memory"]
        prompt = await self.prompt(**x)
        working_memory = working_memory or []
        context = [{"role": "user", "content": prompt}] + working_memory
        if self.use_reflection:
            out = await self.debug({"context": context, "working_memory": working_memory})
        else:
            out = await self.llm(context)
        return out


# ----人类检查代码或者计划----
TASK_REVIEW_INSTRUCTION = """If you want to change, add, delete a task or merge tasks in the plan, say 'change task task_id or current task, ... (things to change)' 
If you confirm the output from the current task and wish to continue, type: confirm"""

CODE_REVIEW_INSTRUCTION = """If you want the codes to be rewritten, say 'change ... (your change advice)' 
If you want to leave it as is, type: confirm"""

EXIT_INSTRUCTION = "If you want to terminate the process, type: exit"

REVIEW_PROMPT = """
This is a <{{trigger}}> review. Please review output from {{latest_action}}"
{{review_instruction}}
{{exit_instruction}}
Please type your review below:
"""


class HumanInput(Action):
    def __init__(self, prompt, **kwargs):
        super().__init__(**kwargs)
        self.prompt = JJPrompt(prompt, **self.kwargs)

    async def run(self, x):
        prompt = await self.prompt(**self.kwargs, **x)
        return input(prompt)


class HumanReview(Action):
    def __init__(self, trigger, review_instruction, exit_instruction, **kwargs):
        super().__init__(**kwargs)
        self.prompt = JJPrompt(
            REVIEW_PROMPT,
            trigger=trigger,
            review_instruction=review_instruction,
            exit_insturction=exit_instruction
        )

    async def run(self, x):
        latest_action = x
        out = await self.prompt({"latest_action": latest_action})
        rsp = input(out)

        if rsp == "exit":
            exit()

        confirmed = "confirm" in rsp

        return rsp, confirmed


class CodeReview(HumanReview):
    def __init__(self, **kwargs):
        super().__init__("code", CODE_REVIEW_INSTRUCTION, EXIT_INSTRUCTION, **kwargs)


class TaskReview(HumanReview):
    def __init__(self, **kwargs):
        super().__init__("task", TASK_REVIEW_INSTRUCTION, EXIT_INSTRUCTION, **kwargs)


PLAN_PROMPT = """
# Context:
{{content}}
# Available Task Types:
{% for task in task_type_desc -%}
    {{ task.name }}: {{ task.desc }} \n
{% endfor %}
# Task:
Based on the context, write a plan or modify an existing plan of what you should do to achieve the goal. A plan consists of one to {max_tasks} tasks.
If you are modifying an existing plan, carefully follow the instruction, don't make unnecessary changes. Give the whole plan unless instructed to modify only one task of the plan.
If you encounter errors on the current task, revise and output the current single task only.
Output a list of jsons following the format:
```json
[
    {
        "instruction": "what you should do in this task, one short phrase or sentence",
        "task_type": "type of this task, should be one of Available Task Types",
    },
    ...
]
```
"""


class Planner(Action):
    def __init__(self, task_type_desc, **kwargs):
        super().__init__(**kwargs)
        self.prompt = JJPrompt(
            PLAN_PROMPT, task_type_desc=task_type_desc, memory=self.memory)
        self.llm = OpenAIBackend(model="gpt-4o", memory=self.memory)

    async def forward(self, x):
        prompt = await self.prompt(x)
        out = await self.llm(prompt)
        print(self.memory)
        return out

class ThinkActObservation(Action):
    def __init__(self,**kwargs):
        self.prompt = JJPrompt(
            PLAN_PROMPT, task_type_desc=task_type_desc, memory=self.memory)

class PlanManager(Action):
    def __init__(self, plans, goal, *args, **kwargs):
        super().__init__(**kwargs)
        for i in plans:
            i["statu"] = "wait"
        self.plans = plans
        self.goal = goal
    async def forward(self, x):

        async def _write_and_exec_code(self, max_retry: int = 3):
            counter = 0
            success = False

            # plan info
            plan_status = self.planner.get_plan_status() if self.use_plan else ""

            # tool info
            if self.tool_recommender:
                context = (
                    self.working_memory.get(
                    )[-1].content if self.working_memory.get() else ""
                )  # thoughts from _think stage in 'react' mode
                plan = self.planner.plan if self.use_plan else None
                tool_info = await self.tool_recommender.get_recommended_tool_info(context=context, plan=plan)
            else:
                tool_info = ""

            # data info
            await self._check_data()

            while not success and counter < max_retry:
                ### write code ###
                code, cause_by = await self._write_code(counter, plan_status, tool_info)

                self.working_memory.add(
                    Message(content=code, role="assistant", cause_by=cause_by))

                ### execute code ###
                result, success = await self.execute_code.run(code)
                print(result)

                self.working_memory.add(
                    Message(content=result, role="user", cause_by=ExecuteNbCode))

                ### process execution result ###
                counter += 1

                if not success and counter >= max_retry:
                    logger.info("coding failed!")
                    review, _ = await self.planner.ask_review(auto_run=False, trigger=ReviewConst.CODE_REVIEW_TRIGGER)
                    if ReviewConst.CHANGE_WORDS[0] in review:
                        counter = 0  # redo the task again with help of human suggestions

            return code, result, success


