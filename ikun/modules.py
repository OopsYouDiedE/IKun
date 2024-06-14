import json

from ikun.core import Module, Prompt, OpenAIBackend, to_message
from ikun.data_parser import parse_code
from ikun.nb_env import ExecuteNbCode

# prompt包括：role，前面几步输入和生成内容，本步示例，以及上一步生成和反馈（如果不是第一次生成）；
# 传入的NbCode只允许使用被分配的那一个Cell
# Optimizer会根据传入代码和生成来反馈。
# Optimizer会返回review和statu；如果正确生成，返回Done；否则返回Undone。
#
from jinja2 import Environment, FileSystemLoader, Template

INTERPRETER_SYSTEM_MSG = """As a data scientist, you need to help user to achieve their goal step by step in a continuous Jupyter notebook. Since it is a notebook environment, don't use asyncio.run. Instead, use await if you need to call an async function."""

STRUCTURAL_PROMPT = """
# Goal
{{goal}}

# Constraints
- You need to write the code to complete the goal perfectly.
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
Output a json following the format:
```json
{
    "reflection": str = "Reflection on previous implementation",
    "improved_impl": str = "Refined code after reflection.",
}
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


class DebugWithReflection(Module):
    def __init__(self):
        self.reflection_sys_msg = REFLECTION_SYSTEM_MSG
        self.reflection = Prompt(
            Template(REFLECTION_PROMPT), debug_example=DEBUG_REFLECTION_EXAMPLE)
        self.check_data = Prompt(Template(CHECK_DATA_PROMPT))
        self.llm = OpenAIBackend(model="gpt-4o")

    async def arun(self, context, working_memory, **kwargs):
        context = [
            to_message(self.reflection_sys_msg, 'system'),
            to_message(
                await self.reflection(
                    debug_example=DEBUG_REFLECTION_EXAMPLE,
                    context=context,
                    previous_impl=working_memory)
            )
        ]

        x = await self.llm(messages=context)
        x = json.loads(parse_code(block=None, text=x))
        return x["improved_impl"]


class WriteAnalysisCode(Module):
    def __init__(self):
        self.first_run_sys_msg = INTERPRETER_SYSTEM_MSG
        self.first_run = Prompt(Template(STRUCTURAL_PROMPT))
        self.llm = OpenAIBackend(model="gpt-4o")
        self.debugger = DebugWithReflection()

    async def arun(self, goal, working_memory=None, use_reflection: bool = False, **kwargs):
        context = [
            to_message(self.first_run_sys_msg, 'system'),
            to_message(await self.first_run(goal=goal))
        ]
        print(context)
        if use_reflection:
            x = await self.debugger(context=context, working_memory=working_memory)
        else:
            x = await self.llm(messages=context)
            print(x)
            x = parse_code(block=None, text=x)
        return x
