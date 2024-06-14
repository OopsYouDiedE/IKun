## IKun：混合特性的小型可拓展框架

---
IKun是一个结合DSPy，Metagpt和MiniChain设计理念的小型框架。IKun能够使用预制和自我生成的工具完成各种任务，并且能够高效的使用过往经验。
IKun着重于在较少人工干预的前提下完成高难度的任务。
IKun具有非常简洁的结构。
IKun将使用Module来代替Action。和MiniChain不同的地方是，IKun将允许自定义优化器对Module的性能进行Prompt优化。
IKun的基础结构有以下几种：
Executor:一个执行命令函数，内部无优化。
Transformer:将信息从一种形式转换到另一种形式；不产生额外信息，只负责转换。
Prompt:一个具有多个参数的数据，可以优化。
目前，将Module看做一种由多个Prompt,Transformer,Executor构成的Chain。
其中像OpenAi之类的大模型是Executor；
格式化器是Transformer；

