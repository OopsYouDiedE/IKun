from __future__ import annotations
import asyncio

from jinja2 import Template


class Action:
    def __init__(self, working_memory=None, memory=None, name=None, **kwargs):
        if not name:
            name = self.__class__.__name__
        self.name = name
        self.working_memory = working_memory
        self.memory = memory
        self.kwargs = kwargs

    async def __call__(self, x):
        out = await self.forward(x)
        if not self.memory is None:
            self.memory.append({"role": self.name, "content": out})
        return out

    async def forward(self, x):
        return NotImplementedError


class OpenAIBackend(Action):
    _aclient = None
    _client = None

    @staticmethod
    def config(**kwargs) -> None:
        from openai import AsyncOpenAI
        OpenAIBackend._aclient = AsyncOpenAI(**kwargs)

    async def forward(self, x):
        response = await self._aclient.chat.completions.create(messages=x, **self.kwargs)
        return response.choices[0].message.content


class JJPrompt(Action):
    def __init__(self, prompt, sys_prompt=None, **kwargs):
        super().__init__(**kwargs)
        self.sys_prompt = sys_prompt
        self.prompt = Template(prompt)

    async def forward(self, x):
        ret = []
        if self.sys_prompt:
            ret.append({'role': 'system', 'content': self.sys_prompt})
        ret.append(
            {'role': 'user', 'content': self.prompt.render(**x, **self.kwargs)})
        return ret


class Sequential(Action):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.steps = args

    async def forward(self, x):
        for step in self.steps:
            x = await step(x)
        return x
