# VRChat integration for Home Assistant

English | [简体中文](https://github.com/hi94740/ha-vrchat/blob/main/README_zh-Hans.md)

Unofficial VRChat integration that adds the status of you and your friends to Home Assistant.

## Requirements

* Home Assistant 2026.3+
* A VRChat account (Log in with third-party account is **NOT** supported. If you only have a platform account (eg. Steam), check out [this guide](https://help.vrchat.com/hc/en-us/articles/360062659053-I-want-to-turn-my-platform-account-through-Steam-Meta-Pico-or-Viveport-into-a-VRChat-account).)

## Setup

1. Download and copy `custom_components/vrchat` folder to `custom_components` folder in your Home Assistant config folder.
2. Restart Home Assistant.
3. Click: [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=vrchat)
Or go to [⚙️ Configuration](https://my.home-assistant.io/redirect/config) > Devices and Services > [🧩 Integrations](https://my.home-assistant.io/redirect/integrations) > [➕ Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=vrchat) > 🔍 Search `VRChat`
4. Follow the instructions to setup your VRChat account.

## Entities

| Name | Type | Description | Picture | Attributes | Yourself | Your friends |
| --- | --- | --- | --- | --- | --- | --- |
| Status | Sensor | User status that aligns with the VRChat website. | The same colored circle you see on the VRChat website that indicates the user's status. ||| ✔️ |
| Status | Select | Same as above. Except it allows you to change your status. | Same as above. || ✔️ ||
| Status description | Sensor | User-defined status text. This sensor will not be added if the user does not have a status description. If you want to change your status description in Home Assistant, use the [Update VRChat status action](#update-vrchat-status-vrchatupdate_user_status). ||| ✔️* | ✔️* |
| In-game presence | Binary sensor | Shows whether the user is logged into the game client or not. ||| ✔️ | ✔️ |
| Location | Sensor | Mostly aligns with the VRChat website. Except it also shows if the user is active on web/mobile or not when user is not in game. | If the user is in a non-private world, shows the world's thumbnail. | If the user is in a non-private world, shows the world's [details](https://vrchat.community/reference/get-world). | ✔️ | ✔️ |
| (User) | Sensor | A sensor with the user's display name as its name, summarizing the above user status and in-game presence. Shows the user's status if the user is in game, and whether the user is active on web/mobile if not in game. | Shows the user's icon/pfp, with avatar image as fallback. | Shows the user's [info](https://vrchat.community/reference/get-user). *Additional attribute:* `friend_of`: ID of the account that have this friend. Useful when you have multiple accounts that have the same friends or are friends of each other. | ✔️ | ✔️ |
| Avatar image | Image |||| ✔️ | ✔️ |
| Location image | Image |||| ✔️ | ✔️ |

(*Some information about a user may not be available. Those entities will not be added. Currently this only seems to affect status description. Location information is intepreted when not available so location entities are always added.)

## Actions

### Update VRChat status `vrchat.update_user_status`

[![Open your Home Assistant instance and show your service developer tools with a specific action selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=vrchat.update_user_status)

Use this action to update your VRChat status and status description.

| Field | Parameter name | Description | Required |
| --- | --- | --- | --- |
| Account | config_entry_id | Choose the VRChat account you want to update status or status description. | ✔️ |
| Status | status | Choose your desired status. Omit this field if you do not want to change your status. ||
| Status description | status_description | Enter your custom status description. Omit this field if you do not want to change your status description. Enter space to clear your status description. ||

## Events

[![Open your Home Assistant instance and show your event developer tools.](https://my.home-assistant.io/badges/developer_events.svg)](https://my.home-assistant.io/redirect/developer_events/)

### `vrchat_event`

All [VRChat websocket events](https://vrchat.community/websocket) is forwarded to the [Home Assistant event bus](https://www.home-assistant.io/docs/automation/trigger/#event-trigger) with a few modifications:

#### Added fields

* `account_id`: ID of the VRChat account that is emitting this event.
* `config_entry_id`: ID of the config entry that is emitting this event.
* `device_id`: If the event is related to a user, this field is set to the ID of the device representing the user.
* `old_user`: If the event is related to a user, this field is set to the [user info](https://vrchat.community/reference/get-user) before this event.

#### Modified fields

* `type`: If the original message does not have this field, it will be set to `error` if the event is an error message (have `err` field), or `unknown` for all other cases.

* `content`: If this field is a json string in the original message, it will be decoded. The decoded content is also modified. See below for details.

#### Modification to `content`

##### Added fields

* `travelingToWorldId`: World ID extracted from `travelingToLocation`

## Using with the VRChat website

The official VRChat website and the interface of this integration in Home Assistant provides different functions so you may want to use them together. Here are some quick ways you can navigate between them.

### Home Assistant ➡️ vrchat.com

Click `⚙ Visit` button in the device info section on the device page representing a VRChat user.

### vrchat.com ➡️ Home Assistant

We have to use a userscript to modify the website to make this possible:

1. Setup a userscript manager (eg. [Tampermonkey](https://www.tampermonkey.net), [Userscripts](https://itunes.apple.com/us/app/userscripts/id1463298887)) for your browser.
2. Install [this userscript](https://gist.githubusercontent.com/hi94740/b954be984639ff5246db9e69eb9f7622/raw/vrchat-ha.user.js).
3. Go to [vrchat.com](vrchat.com).
4. Enter your Home Assistant connection info. (This is needed because Home Assistant assigns random IDs to devices, and we need to get those IDs from Home Assistant to link users to device pages.)
5. Choose whether you want to open in [Home Assistant Companian app](https://companion.home-assistant.io) or in browser.
6. You can now use `HA` buttons on user page and `HA` links in side bar to go to device pages in Home Assistant. You can use the `⚙ HA` button in side bar to reconfigure.

#### Userscript config

| Field | Description | Required |
| --- | --- | --- |
| Home Assistant URL | Base URL to access your Home Assistant server. (eg. http://homeassistant.local:8123) | ✔️ |
| Alternative Home Assistant URL | If you have a different URL to access your Home Assistant server when not connected to your home WiFi, you can enter it here. ||
| Home Assistant access token | You can create a [long-lived access token](https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token) at the bottom of this page: [![Open your Home Assistant instance and show your Home Assistant user's security options.](https://my.home-assistant.io/badges/profile_security.svg)](https://my.home-assistant.io/redirect/profile_security/) | ✔️ |
| Open in app? | If you have [Home Assistant Companian app](https://companion.home-assistant.io) installed and you want to open device pages in app, choose `OK`. If not or you want to open in browser, choose `Cancel`. | ✔️ |