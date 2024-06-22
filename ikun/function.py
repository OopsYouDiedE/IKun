import json

import re


async def transform_text(x):
    segments = re.split(r'(```.*?```)', x, flags=re.DOTALL)
    result = []

    for segment in segments:
        segment = segment.strip()
        if segment.startswith('```') and segment.endswith('```'):
            code_type = re.match(r'```(\w+)', segment).group(1)
            code_content = segment[len(f'```{code_type}') + 1: -3].strip()
            result.append({"type": code_type, "content": code_content})
        else:
            result.extend({"type": "markdown", "content": line.strip()}
                          for line in segment.split('\n') if line.strip())
    return result


async def text_to_json(x):
    if type(x) is str:
        return json.dumps(x)
    elif type(x) is list:
        for i in x:
            if i["type"] == "json":
                i["data"] = json.loads(i["content"])
        return x


async def higher(x):
    return [x]


async def lower(x):
    return x[0]


async def chats_to_str(x):
    rsp = [i["role"]+i["content"]for i in x]