# VRChat Home Assistant 集成

[English](https://github.com/hi94740/ha-vrchat/blob/main/README.md) | 简体中文

这是一个非官方的 VRChat 集成，可将你和好友的状态添加到 Home Assistant 中。

## 要求

* Home Assistant 2026.3+
* VRChat 账号（**不支持**使用第三方账号登录。\n如果你只有平台账号（比如 Steam），请参考[此教程](https://help.vrchat.com/hc/en-us/articles/360062659053-I-want-to-turn-my-platform-account-through-Steam-Meta-Pico-or-Viveport-into-a-VRChat-account)将其转换为 VRChat 账号。）

## 安装和配置

1. 下载并复制 `custom_components/vrchat` 文件夹到 Home Assistant 配置文件夹中的 `custom_components` 目录下。
2. 重启 Home Assistant。
3. 点击：[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=vrchat)
或前往 [⚙️ 配置](https://my.home-assistant.io/redirect/config) > 设备与服务 > [🧩 集成](https://my.home-assistant.io/redirect/integrations) > [➕ 添加集成](https://my.home-assistant.io/redirect/config_flow_start?domain=vrchat) > 🔍 搜索 `VRChat`
4. 跟随指引设置你的 VRChat 账号。

## 实体

| 名称 | 类型 | 描述 | 图片 | 属性 | 本人 | 好友 |
| --- | --- | --- | --- | --- | --- | --- |
| 状态 | 传感器 | 与 VRChat 官网一致的用户状态。 | 显示与 VRChat 官网相同的状态颜色圆点。 |  |  | ✔️ |
| 状态 | 选择 | 同上。但允许你更改自己的状态。 | 同上。 |  | ✔️ |  |
| 状态描述 | 传感器 | 用户定义的状态描述文本。如果用户未设置状态描述，则不会添加此实体。若要更改自己的状态描述，请使用[更新 VRChat 状态动作](#更新-vrchat-状态)。 |  |  | ✔️* | ✔️* |
| 游戏在线状态 | 二元传感器 | 显示用户是否已登入游戏客户端。 |  |  | ✔️ | ✔️ |
| 位置 | 传感器 | 基本与 VRChat 官网同步。此外，当用户不在游戏中时，还会显示其是否在网页/移动端活跃。 | 如果用户处于非私密世界，则显示该世界的缩略图。 | 如果用户处于非私密世界，显示该世界的[详细信息](https://vrchat.community/reference/get-world)。 | ✔️ | ✔️ |
| (用户) | 传感器 | 以用户昵称命名的传感器，汇总了上述状态和游戏在线信息。用户登入游戏时显示状态，不在游戏中时则显示用户是否在网页/移动端活跃。 | 显示用户头像，若用户未设置头像则显示虚拟形象图片。 | 显示用户的[详细信息](https://vrchat.community/reference/get-user)。*额外属性：* `friend_of`：拥有此好友的账号 ID。当你设置了多个账号并且有重叠好友时可用于区分。 | ✔️ | ✔️ |
| 当前虚拟形象 | 图像 |  |  |  | ✔️ | ✔️ |
| 当前位置图片 | 图像 |  |  |  | ✔️ | ✔️ |

(*用户可能会缺失某些信息，对应的实体将不会被添加（目前似乎仅影响状态描述）。位置信息在缺失时会被推断处理，因此位置实体始终会被添加。)

## 动作

### 更新 VRChat 状态 `vrchat.update_user_status`

[![Open your Home Assistant instance and show your service developer tools with a specific action selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=vrchat.update_user_status)

使用此动作更新你的 VRChat 状态和状态描述。

| 字段 | 参数名称 | 描述 | 是否必填 |
| --- | --- | --- | --- |
| 账号 | config_entry_id | 选择要更新状态或描述的 VRChat 账号。 | ✔️ |
| 状态 | status | 选择你想要的状态。留空则不更改。 |  |
| 状态描述 | status_description | 输入自定义状态文本。留空则不更改。输入空格可清除当前状态描述。 |  |

## 事件

### `vrchat_event`

所有 [VRChat websocket 事件](https://vrchat.community/websocket) 都会被转发到 [Home Assistant 事件总线](https://www.home-assistant.io/docs/automation/trigger/#event-trigger)，并带有以下修改：

#### 增加字段

* `account_id`: 发送此事件的 VRChat 账号 ID。
* `config_entry_id`: 发送此事件的配置条目 ID。
* `device_id`: 如果此事件与某个用户相关，此字段将包含该用户对应的设备 ID。
* `old_user`: 如果此事件与某个用户相关，此字段将包含事件发生之前的[用户信息](https://vrchat.community/reference/get-user)。

#### 修改字段

* `type`: 如果原始消息没有此字段，若消息是错误信息（带有`err`字段）则设为 `error`，其他情况设为 `unknown`。
* `content`: 如果原始消息中的此字段是 JSON 字符串，它将被解码。

#### 对 `content` 的修改

##### 增加字段

* `travelingToWorldId`: 从 `travelingToLocation` 中提取的世界 ID。

## 搭配 VRChat 官网使用

VRChat 官网与此集成在 Home Assistant 中的界面功能各异，你可以搭配使用。以下是快速在二者之间跳转的方法：

### Home Assistant ➡️ vrchat.com

在 Home Assistant 中代表 VRChat 用户的设备页面上，点击设备信息部分的 `⚙ 访问` 按钮。

### vrchat.com ➡️ Home Assistant

需要使用用户脚本（Userscript）修改网页来实现：

1. 在浏览器安装用户脚本管理器（例如 [Tampermonkey](https://www.tampermonkey.net), [Userscripts](https://itunes.apple.com/us/app/userscripts/id1463298887)）。
2. 安装[此脚本](https://gist.githubusercontent.com/hi94740/b954be984639ff5246db9e69eb9f7622/raw/vrchat-ha.user.js)。
3. 打开 [vrchat.com](https://vrchat.com)。
4. 输入你的 Home Assistant 连接信息（由于 Home Assistant 的设备 ID 是随机生成的，脚本需要从 Home Assistant 获取 ID 信息以生成链接）。
5. 选择在 [Home Assistant Companian app](https://companion.home-assistant.io) 或浏览器中打开。
6. 你现在可以使用用户页面上的 `HA` 按钮和侧边栏的 `HA` 链接跳转到 Home Assistant 的设备页面。点击侧栏中的 `⚙ HA` 按钮可重新配置。

#### 用户脚本配置项

| 字段 | 描述 | 是否必填 |
| --- | --- | --- |
| Home Assistant URL | 访问 Home Assistant 服务器的基础地址（例如 http://homeassistant.local:8123）。 | ✔️ |
| Alternative Home Assistant URL | 如果有外网访问地址可填入。 |  |
| Home Assistant access token | 可以在此页面最下方创建一个[长期访问令牌](https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token)：[![Open your Home Assistant instance and show your Home Assistant user's security options.](https://my.home-assistant.io/badges/profile_security.svg)](https://my.home-assistant.io/redirect/profile_security/) | ✔️ |
| Open in app? | 如果你安装了 [Home Assistant Companian app](https://companion.home-assistant.io) 并希望跳转到 app，选择 `好` / `确定`。否则选择 `取消`，这样会在浏览器中打开设备页面。 | ✔️ |

## 推送通知

你可以添加以下蓝图，用于创建当指定实体状态变化时向指定移动设备发送推送通知的自动化:
[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgist.githubusercontent.com%2Fhi94740%2F9d4e8a98b03e05038113359cf8f0451e%2Fraw)