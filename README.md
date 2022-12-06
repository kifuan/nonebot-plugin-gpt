# nonebot-plugin-gpt

一个调用 `ChatGPT` 的聊天插件，它可以为不同的群聊分别保存聊天状态。

这意味着，不同的群聊之间，聊天记录的上下文都是**相互独立**的。

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
+ `GPT_PROBABILITY`：回复普通消息的概率，默认为0，也就是不回复。我觉得这个功能其实不太好，但是考虑到某些人可能想要以这种方式与机器人互动，还是加上了这个配置项，并且必须你手动开启。


## 使用

+ `/gpt {message}`

  聊天，这个没什么好介绍的。

+ `/gpt_control {action}`

  在 `GPT_SUDOERS` 中的用户可以控制此机器人，有下列两个`action`：

  + `refresh_session`：刷新 `session`，根据 `ChatGPT` 下的 [issue #11](https://github.com/acheong08/ChatGPT/issues/11)，你填写的 `session` 应当有一个月的有效期。
  + `reset_status`：刷新聊天记录的上下文。
