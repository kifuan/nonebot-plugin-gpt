# nonebot-plugin-gpt

一个调用 `ChatGPT` 的聊天插件，它可以为不同的**群聊或者用户**分别保存聊天状态。

这意味着，不同的群聊和用户私聊之间，聊天记录的上下文都是**相互独立**的。

例如，**A群**的聊天信息只是**A群**共享的，而**B用户**和**C群**和**A群**的上下文没有任何关系。这是为了有更好的体验，因为同一个群聊的聊天记录大家都能看见。

当文本过长时，它会以**图片**的形式返回，这是为了防止发送的消息太长被风控。

## 安装

+ 使用 `pip` 安装：
  
  ```bash
  pip install -U nonebot-plugin-gpt
  ```


## 配置项

下方的配置项都要在 `.env` 中配置，请参考 [Nonebot 文档](https://v2.nonebot.dev/docs/tutorial/configuration#%E9%85%8D%E7%BD%AE%E6%96%B9%E5%BC%8F)。

| 名称                             | 类型              | 默认值                       | 描述                                                                                                                                                           |
|--------------------------------|-----------------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GPT_SESSION_TOKEN`            | `str`           | **必填**                    | 在 [https://chat.openai.com/chat](https://chat.openai.com/chat) 下，把 `F12` -> `Application` -> `Cookies` -> `__Secure-next-auth.session-token` 的内容复制下来，填入此配置项。 |
| `GPT_API_KEY`                  | `str`           | **必填**                    | 到 [https://beta.openai.com/account/api-keys](https://beta.openai.com/account/api-keys) 生成你的 `API Key`，填入此配置项。                                                |
| `GPT_SUDOERS`                  | `list[int]`     | **必填**                    | 一个有权限控制此机器人的QQ号列表，例如`[123, 456]`。                                                                                                                            |
| `GPT_API_BASEURL`              | `str`           | `https://chat.openai.com` | 你可以用这个配置反代，默认使用官方链接，也就是不走代理。                                                                                                                                 |
| `GPT_PROXY`                    | `Optional[str]` | `None`                    | 代理，为 `None` 即默认情况不走代理。                                                                                                                                       |
| `GPT_TIMEOUT`                  | `int`           | `300`                     | 超时时间，单位为秒。                                                                                                                                                   |
| `GPT_PROBABILITY`              | `float`         | `0`                       | 回复普通消息的概率，默认为 `0` 概率，也就是不回复。我觉得这个功能其实不太好，但是考虑到某些人可能想要以这种方式与机器人互动，还是加上了这个配置项，并且必须你手动开启。                                                                       |
| `GPT_REQUEST_MINIMAL_INTERVAL` | `int`           | `5`                       | 每个请求最短的间隔，单位为秒。为了尽可能地防止频繁请求，最好有这样一个间隔。当然你完全可以把它设置为 `0` 秒。                                                                                                    |
| `GPT_IMAGE_TEXT_LENGTH`        | `int`           | `150`                     | 当文本长度大于等于这个数字时，会被转为图片发送。                                                                                                                                     |
| `GPT_IMAGE_FONT`               | `Optional[str]` | `None`                    | 图片文本的字体，默认为本项目内置的思源黑体。                                                                                                                                       |
| `GPT_IMAGE_FONT_SIZE`          | `int`           | `20`                      | 字体大小。                                                                                                                                                        |
| `GPT_IMAGE_LINE_WIDTH`         | `int`           | `500`                     | 每行宽度。                                                                                                                                                        |
| `GPT_IMAGE_PADDING`            | `int`           | `20`                      | 图片四周的空白大小，以及每行之间的间距。                                                                                                                                         |

## 使用

> 除了概率触发的消息以外，下列均以 `on_command` 方式定义。如果您自己设置过 `command_start` 或其它相关配置，请根据您的配置进行调整。
> 默认来说，它应该是以斜线 `/` 开头的。

+ `/gpt {message}`
  聊天。注意，用户无需输入花括号，这里只是为了方便说明，它是一个消息。

  如果接受消息时 `token` 过期，它会尝试自动刷新，并通知由于这个错误而请求失败的群聊或私聊。

+ `/gpt_control {action}`

  在 `GPT_SUDOERS` 中的用户可以控制此机器人，有下列两个`action`：

  + `refresh_session`：刷新 `session`，根据我的使用，貌似这个 `token` 的有效期只有一天，准确时间不确定。
  + `reset_context`：刷新聊天记录的上下文。

+ 当 `GPT_PROBABILITY` 不为 `0` 时，有概率回复你发的普通消息。但是如果没有文本，例如只发了图片或聊天记录，它是不会回复的。
