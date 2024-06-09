"""
Module，是只有一种输入，一种输出的模型。Module只会产生结果，以及报错两种模式；产生结果则传给下一级，报错则返回上一级。
对于Module的训练也就是对于Prompt的训练。通过优化Prompt来产出更加稳定的输出。
而Module是一种固定模式的pipeline。
在训练过程中，优化器会根据策略，分步对模型中的全部Module进行合理的优化；
这种优化更类似于强化学习；
在这里，最基础的不是Tensor，而是象征着信息传递的Information。
包括Prompt，也是一种Information。
不论是初始化的权重，还是Prompt，还是传入的信息，都是Information。
"""

from openai import OpenAI, AsyncOpenAI
from nbformat import v4 as nbf
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
import nbformat


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


class SinglePass:
    def __init__(self, LM) -> None:
        """这里，没有prompt，所有信息将会不经过额外处理转化为Message传递过去，输出为text形式的Infomation。"""
        pass

    def foward(self, x) -> str:
        return


class ExecutingCode:
    """执行ChatGPT生成的代码，其他部分标记为Markdown，python代码部分为Code；"""

    def run(self, x):
        """输入为chatgpt生成的代码，其中用`包裹的代码块解读为Code，而其他部分为Markdown。使用nbclient运行每一个代码块，不论正常执行还是报错都将信息返回。"""
        cells = parse_input(x)
        return execute_notebook(cells)


class MultipuleChangeContext:
    """能够根据反馈优化Output，包括一个初始化，一个修改，一个输出。"""

    def __init__(self) -> None:
        pass


api_key = "sk-cRk2eMr7OMij3FKyD4C41a291c9943018728C3D479Dd1e99"
base_url = "https://chatapi.onechats.top/v1/"


class OpenAIBackend:
    @staticmethod
    def config(**kwargs) -> None:
        from openai import OpenAI, AsyncOpenAI
        OpenAIBackend.client = OpenAI(**kwargs)
        OpenAIBackend.aclient = AsyncOpenAI(**kwargs)

    def __init__(self) -> None:
        pass

    def run(self, message) -> str:
        response = self.client.chat.completions.create()
        return response.choices[0].message.content
