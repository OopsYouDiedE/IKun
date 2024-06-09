from openai import OpenAI, AsyncOpenAI
from jinja2 import Environment, FileSystemLoader, Template
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

    def run(self, **kwargs) -> str:
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class SinglePass:
    def __init__(self, LM) -> None:
        """这里，没有prompt，所有信息将会不经过额外处理转化为Message传递过去，输出为text形式的Infomation。"""
        pass

    def foward(self, x) -> str:
        return


"""
写一个数据解释器的Module。
要求，首先根据要求生成初始步骤；
然后逐步执行；在需要的时候询问用户；
在执行完成之后还要保存；
生成内容一般为串行；
修改器是另一个Net；
"""


class Planning:
    """
    使用LoadExperience，Planning根据用户提的需求；
    输入为requirement；
    输出为plan；
    planAndAct相当于多轮对话；其中Act相当于用户反馈。
    """


class Datainterpreter:
    def forward:
