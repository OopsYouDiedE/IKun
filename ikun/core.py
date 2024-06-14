from __future__ import annotations
import asyncio


class Module:
    async_mode = False

    async def __call__(self, **kwargs):
        return await self.arun(**kwargs)

    def _run(self, x, **kwargs):
        return asyncio.run(self.arun(**kwargs))

    async def arun(self, **kwargs):
        raise NotImplementedError


class OpenAIBackend(Module):
    _aclient = None
    _client = None

    @staticmethod
    def config(**kwargs) -> None:
        from openai import OpenAI, AsyncOpenAI
        OpenAIBackend._client = OpenAI(**kwargs)
        OpenAIBackend._aclient = AsyncOpenAI(**kwargs)

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    async def arun(self, messages, **kwargs):
        response = await self._aclient.chat.completions.create(messages=messages, **self.kwargs)
        return response.choices[0].message.content


class Prompt(Module):

    def __init__(self, prompt, **kwargs) -> None:
        self.prompt = prompt
        self.kwargs = kwargs

    async def arun(self, **kwargs):
        return self.prompt.render(**self.kwargs, **kwargs)


def to_message(x, start_tag="user"):
    return {"role": start_tag, "content": x}

# 1.传入任务，设计代码执行；执行完成后由Optimizer验证，输入到pase_next。
