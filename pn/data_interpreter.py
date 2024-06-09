"""
包含组件：plan，
"""
from pathlib import Path
from typing import Union, List, Dict

from jinja2 import Template, Environment, FileSystemLoader

api_key = "sk-cRk2eMr7OMij3FKyD4C41a291c9943018728C3D479Dd1e99"
base_url = "https://chatapi.onechats.top/v1/"


class OpenAIBackend:
    _aclient = None
    _client = None

    @staticmethod
    def config(**kwargs) -> None:
        from openai import OpenAI, AsyncOpenAI
        OpenAIBackend._client = OpenAI(**kwargs)
        OpenAIBackend._aclient = AsyncOpenAI(**kwargs)

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    async def run(self, messages) -> str:
        response = self._client.chat.completions.create(messages=messages, **self.kwargs)
        return response.choices[0].message.content

    async def arun(self, messages) -> str:
        response = await self._aclient.chat.completions.create(messages=messages, **self.kwargs)
        return response.choices[0].message.content


import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from nbformat import v4 as nbf


def parse_input(x):
    """
    将输入的字符串解析为notebook单元列表。

    参数：
        x (str): 包含代码和Markdown的字符串。

    返回：
        cells (list): 包含nbformat单元的列表。
    """
    cells = []
    lines = x.split('\n')
    in_code_block = False
    code_block = []
    markdown_block = []

    for line in lines:
        if line.strip().startswith('```') and in_code_block:
            # 结束代码块
            in_code_block = False
            if code_block:
                cells.append(nbf.new_code_cell('\n'.join(code_block)))
                code_block = []
        elif line.strip().startswith('```python') and not in_code_block:
            # 开始代码块前，先添加任何已收集的Markdown，注意，```python
            in_code_block = True
            if markdown_block:
                cells.append(nbf.new_markdown_cell('\n'.join(markdown_block)))
                markdown_block = []
        elif in_code_block:
            # 收集代码行
            code_block.append(line)
        else:
            # 收集Markdown行
            markdown_block.append(line)

    # 添加最后的Markdown块（如果有的话）
    if markdown_block:
        cells.append(nbf.new_markdown_cell('\n'.join(markdown_block)))

    return cells


def execute_notebook(cells):
    """
    执行notebook中的代码单元，并返回执行结果。

    参数：
        cells (list): 包含nbformat单元的列表。

    返回：
        output (str): notebook执行结果。
    """
    # 创建一个新的 notebook
    nb = nbf.new_notebook()
    nb.cells = cells

    # 写入到临时文件
    with open('temp_notebook.ipynb', 'w') as f:
        nbformat.write(nb, f)

    # 运行 notebook
    client = NotebookClient(nb)
    try:
        client.execute()
    except CellExecutionError as e:
        return f"Execution error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

    # 收集执行结果
    output = []
    for cell in client.nb.cells:
        if cell.cell_type == 'code':
            for out in cell.outputs:
                if 'text' in out:
                    output.append(out['text'])
                if 'data' in out and 'text/plain' in out['data']:
                    output.append(out['data']['text/plain'])
        else:
            pass
            # output.append(cell.source)

    return '\n'.join(output)


class ExecutingCode:
    """执行ChatGPT生成的代码，其他部分标记为Markdown，python代码部分为Code；"""

    def run(self, x):
        """输入为chatgpt生成的代码，其中用`包裹的代码块解读为Code，而其他部分为Markdown。使用nbclient运行每一个代码块，不论正常执行还是报错都将信息返回。"""
        cells = parse_input(x)
        return execute_notebook(cells)


class Module:
    def __init__(self):
        pass

    def forward(self):
        pass


class SinglePasser:
    """只有初始化的prompt设定，以及forward生成内容。"""

    def __init__(self, backend: OpenAIBackend, prompt: Template = None, system: str = None, **kwargs):
        self.system = system
        self.prompt = prompt
        self.backend = backend
        self.kwargs = kwargs

    async def forward(self, query: str):
        messages: list[dict[str, str]] = []
        if self.system:
            messages.append({'role': 'system', 'content': self.system})
        if self.prompt:
            new_query = self.prompt.render(query=query, **self.kwargs)
            messages.append({'role': 'users', 'content': new_query})

        return await self.backend.arun(messages)


class CoT(SinglePasser):

    def __init__(self, backend: OpenAIBackend, prompt: Template = None, **kwargs):
        if not prompt:
            prompt = Environment(loader=FileSystemLoader(".")).get_template(
                "../prompt_weights/cot.j2"
            )
        super().__init__(backend, prompt, **kwargs)

    async def forward(self, query: str):
        answer=await super().forward(query)
        

