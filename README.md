# [Skins](https://github.com/deathaxe/sublime-skins)

[![License](https://img.shields.io/github/license/deathaxe/sublime-skins.svg?style=flat-square)](LICENSE)
[![Package Control](https://img.shields.io/packagecontrol/dt/Skins.svg?style=flat-square)](https://packagecontrol.io/packages/Skins)

**Skins** gives users the ability to change their current **Sublime Text** color scheme and theme with a single command. When a skin is selected, a certain set of settings is applied to Sublime Text. Skins can be provided in theme packages such as [Boxy Theme](https://github.com/ihodev/sublime-boxy) or they can be created by users themselves by saving the current settings to a new User Skin.

![screenshot](https://cloud.githubusercontent.com/assets/16542113/25050093/aae66aa0-2145-11e7-9edd-acd019ac5610.gif)

### End Users

#### General Usage

1. Open the Command Palette
2. Type one of the following three commands:
  * `UI: Select Skin`
  * `UI: Save Skin`
  * `UI: Delete Skin`.

##### Keyboard shortcuts

To quickly open the `UI: Select Skin` menu use:

* <kbd>Ctrl+F12</kbd> on Windows / Linux
* <kbd>Super+F12</kbd> on macOS

#### Settings

By default the following settings are stored by `Save User Skin`

* `color_scheme`
* `theme`
* `font_face`
* `font_size`

To edit the settings

1. Open the Command Palette
2. Type `Preferences: Skins Settings`

The settings are stored in `Packages/User/Skins.sublime-settings`.

**Example**

```javascript
"skin-template":
{
    // List of settings to load from / save to Preferences.sublime-settings
    "Preferences":
    [
        "color_scheme",
        "theme",
        "font_face",
        "font_size"
    ],
    // List of settings to load from / save to SublimeLinter.sublime-settings
    "SublimeLinter":
    {
        "user":
        [
            "error_color",
            "gutter_theme",
            "warning_color"
        ]
    }
}
```

### Theme Developers

#### General

**Skins** parses all `*.skins` files in all packages. They are expected to store a collection of settings for sublime text and other packages. More than one skins file can exist in a package. The name of the file does not matter, but the names of the skins inside must be unique per package. The quick panel will show these names. The `Package` providing it is displayed in the second row as a kind of description.

#### File Format

```javascript
{
    // skin
    "Boxy Tomorrow (Green)": {
        // Packages/User/Preferences.sublime-settings
        "Preferences": {
            "color_scheme": "Packages/Boxy Theme/schemes/Boxy Tomorrow.tmTheme",
            "theme": "Boxy Tomorrow.sublime-theme",
            "theme_accent_green" : true,
            "theme_accent_orange": null,
            "theme_accent_purple": null
        },
        // Packages/User/SublimeLinter.sublime-settings
        "SublimeLinter": {
            "user": {
                // ...
            }
        }
    },

    // skin
    "Monokai 2": {
        // ...
    },

    // ...
}
```

Each child node of a skin represents the settings to be written to a `Packages/User/*.sublime-settings` file. Therefore settings can be provided not only for `Sublime Text` but for any installed package such as `SublimeLinter`. A skin must at least contain the `Preferences` node with `color_scheme` and `theme` settings to be valid but may include any other setting accepted by `Sublime Text`.

Settings with `null` value, are deleted in the sublime-settings files.

#### Commands

`Skins` exports the following `commands` to directly interact with all available skins. They can be used to create key bindings or command shortcuts to the most frequent used skins.

##### Set Skins

To open a quick panel with all available skins call:

```javascript
"command": "set_skin"
"args": { }
```

To open a quick panel with all skins provided by a single package call:

```javascript
"command": "set_skin",
"args": { "package": "Skins" }
```

To directly apply a certain predefined skin call:

```javascript
"command": "set_skin",
"args": { "package": "Skins", "name": "Monokai" }
```

To apply a saved user skin call:

```javascript
"command": "set_skin",
"args": { "package": "User", "name": "Preset 01" }
```


##### Save Skins

The following example will directly save the current look and feel as `Preset 01` in the `Packages/User/Saved Skins.skins` file.

```javascript
"command": "save_user_skin",
"args": { "name": "Preset 01" }
```

##### Delete Skins

The following example will directly delete `Preset 01` from the `Packages/User/Saved Skins.skins` file.

```javascript
"command": "delete_user_skin",
"args": { "name": "Preset 01" }
```

### Inspired by

* [`chmln/Theme Menu Switcher`](https://github.com/chmln/sublime-text-theme-switcher-menu)
* [`chrislongo/QuickThemes`](https://github.com/chrislongo/QuickThemes)
