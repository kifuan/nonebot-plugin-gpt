# nonebot-plugin-gpt

一个调用 `ChatGPT` 的聊天插件，它可以为不同的**群聊或者用户**分别保存聊天状态。

这意味着，不同的群聊和用户私聊之间，聊天记录的上下文都是**相互独立**的。

例如，**A群**的聊天信息只是**A群**共享的，而**B用户**和**C群**和**A群**的上下文没有任何关系。这是为了有更好的体验，因为同一个群聊的聊天记录大家都能看见。

## 安装

+ 使用 `pip` 安装：
  
  ```bash
  pip install -U nonebot-plugin-gpt
  ```


## 配置项

关于如何配置，请参考 [Nonebot 文档](https://v2.nonebot.dev/docs/tutorial/configuration#%E9%85%8D%E7%BD%AE%E6%96%B9%E5%BC%8F)。

+ `GPT_SESSION_TOKEN`: 在 [https://chat.openai.com/chat](https://chat.openai.com/chat) 下，把 `F12` -> `Application` -> `Cookies` -> `__Secure-next-auth.session-token` 的内容复制下来，填入此配置项。
+ `GPT_API_KEY`：到 [https://beta.openai.com/account/api-keys](https://beta.openai.com/account/api-keys) 生成你的 `API Key`，填入此配置项。
+ `GPT_SUDOERS`：一个有权限控制此机器人的QQ号列表，例如`[123, 456]`。
+ `GPT_PROBABILITY`：回复普通消息的概率，默认为 `0`，也就是不回复。我觉得这个功能其实不太好，但是考虑到某些人可能想要以这种方式与机器人互动，还是加上了这个配置项，并且必须你手动开启。


## 使用

> 除了概率触发的消息以外，下列均以 `on_command` 方式定义。如果您自己设置过 `command_start` 或其它相关配置，请根据您的配置进行调整。

+ `gpt {message}`

+ `gpt_control {action}`

  在 `GPT_SUDOERS` 中的用户可以控制此机器人，有下列两个`action`：

  + `refresh_session`：刷新 `session`，根据 `ChatGPT` 下的 [issue #11](https://github.com/acheong08/ChatGPT/issues/11)，你填写的 `session` 应当有一个月的有效期。
  + `reset_status`：刷新聊天记录的上下文。

+ 当 `GPT_PROBABILITY` 不为 `0` 时，有概率回复你发的普通消息。但是如果没有文本，例如只发了图片或聊天记录，它是不会回复的。
