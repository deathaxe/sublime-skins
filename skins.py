# coding: utf-8
import os.path
import sublime
import sublime_plugin

PREF = "Preferences"
PREF_EXT = ".sublime-settings"
PREF_USER = PREF + PREF_EXT
PREF_SKIN = "Skins" + PREF_EXT


def decode_resource(name):
    """Load and decode sublime text resource.

    Arguments:
        name    - Name of the resource file to load.

    returns:
        This function always returns a valid dict object of the decoded
        resource. The returned object is empty if something goes wrong.
    """
    try:
        return sublime.decode_value(sublime.load_resource(name)) or {}
    except Exception as e:
        message = "Skins: loading %s failed with %s" % (name, e)
        sublime.status_message(message)
        print(message)
    return {}


def validate_skin(skin_data):
    """Check skin integrity and return the boolean result.

    For a skin to be valid at least 'color_scheme' and 'theme' must exist.
    Otherwise SublimeText's behavior when loading the skin is unpredictable.

    SublimeLinter automatically creates and applies patched color schemes if
    they doesn't contain linter icon scopes. To ensure not to break this
    feature this function ensures not to apply such a hacked color scheme
    directly so SublimeLinter can do his job correctly.

    Arguments:
        skin_data - JSON object with all settings to apply for the skin.
    """
    # check theme file
    theme_name = os.path.basename(skin_data[PREF]["theme"])
    theme_ok = any(sublime.find_resources(theme_name))
    # check color scheme
    path, tail = os.path.split(skin_data[PREF]["color_scheme"])
    name = tail.replace(" (SL)", "")
    color_schemes = sublime.find_resources(name)
    if not color_schemes:
        return False
    # Try to find the exact path from *.skins file
    resource_path = "/".join((path, name))
    for found in color_schemes:
        if found == resource_path:
            return theme_ok
    # Use the first found color scheme which matches 'name'
    skin_data[PREF]["color_scheme"] = color_schemes[0]
    return theme_ok


def load_user_skins():
    """Open the 'Saved Skins.skins' and read all valid skins from it."""
    return {name: data
            for name, data in decode_resource(
                "Packages/User/Saved Skins.skins").items()
            if validate_skin(data)}


def save_user_skins(skins):
    """Save the skins to the 'Saved Skins.skins'."""
    user_skins_file = os.path.join(
        sublime.packages_path(), "User", "Saved Skins.skins")
    with open(user_skins_file, "w", encoding="utf-8") as file:
        file.write(sublime.encode_value(skins, True))


class SetSkinCommand(sublime_plugin.WindowCommand):
    """Implements the 'set_skin' command."""

    # A sublime.Settings object of the global Sublime Text settings
    prefs = None

    # The last selected row index - used to debounce the search so we
    # aren't apply a new theme with every keypress
    last_selected = -1

    def run(self, package=None, name=None):
        """Apply all visual settings stored in a skin.

        If 'set_skin' is called with both args 'package' and 'name',
        the provided information will be used to directly switch to
        the desired skin.

            sublime.run_command("set_skin", {
                "Package": "User", "name": "Preset 1"})

        If at least one of the args is not a string, a quick panel with all
        available skins is displayed.

            sublime.run_command("set_skin")

        Arguments:
            package (string): name of the package providing the skin or (User)
            name (string): name of the skin in the <skins>.skins file
        """
        if not self.prefs:
            self.prefs = sublime.load_settings(PREF_USER)

        # directly apply new skin
        if isinstance(package, str) and isinstance(name, str):
            for skins_file in sublime.find_resources("*.skins"):
                if package in skins_file:
                    skin = decode_resource(skins_file).get(name)
                    if validate_skin(skin):
                        return self.set_skin(package, name, skin)
        # prepare and show quick panel asynchronous
        sublime.set_timeout_async(self.show_quick_panel)

    def show_quick_panel(self):
        """Display a quick panel with all available skins."""
        initial_skin = self.prefs.get("skin")
        initial_selected = -1
        # a dictionary with all preferences to restore on abort
        initial_prefs = {}
        # the icon to display next to the skin name
        icon = "💦 "
        # the package and skin name to display in the quick panel
        items = []
        # the skin objects with all settings
        skins = []

        # Create the lists of all available skins.
        for skins_file in sublime.find_resources("*.skins"):
            package = skins_file.split("/", 2)[1]
            for name, skin in decode_resource(skins_file).items():
                if validate_skin(skin):
                    if initial_skin == "/".join((package, name)):
                        initial_selected = len(items)
                    items.append([icon + name, package])
                    skins.append(skin)

        def on_done(index):
            """Apply selected skin if user pressed enter or revert changes.

            Arguments:
                index (int): Index of the selected skin if user pressed ENTER
                    or -1 if user aborted by pressing ESC.
            """
            if index == -1:
                for key, val in initial_prefs.items():
                    if val:
                        self.prefs.set(key, val)
                    else:
                        self.prefs.erase(key)
                sublime.save_settings(PREF_USER)
                return
            name, package = items[index]
            self.set_skin(package, name.strip(icon), skins[index])

        def on_highlight(index):
            """Temporarily apply new skin, if quick panel selection changed.

            Arguments:
                index (int): Index of the highlighted skin.
            """
            if index == -1:
                return

            self.last_selected = index

            def preview_skin():
                # The selected row has changed since the timeout was created.
                if index != self.last_selected:
                    return
                for key, val in skins[index][PREF].items():
                    # backup settings before changing the first time
                    if key not in initial_prefs:
                        initial_prefs[key] = self.prefs.get(key)
                    if val:
                        self.prefs.set(key, val)
                    else:
                        self.prefs.erase(key)
            # start timer to delay the preview a little bit
            sublime.set_timeout_async(preview_skin, 250)

        self.window.show_quick_panel(
            items=items, selected_index=initial_selected,
            flags=sublime.KEEP_OPEN_ON_FOCUS_LOST,
            on_select=on_done, on_highlight=on_highlight)

    def set_skin(self, package, name, skin):
        """Apply all skin settings.

        Arguments:
            package (string): name of the package providing the skin or (User)
            name (string): name of the skin in the <skins>.skins file
            skin (dict): all settings to apply
        """
        self.prefs.set("skin", "/".join((package, name)))
        for pkg_name, pkg_prefs in skin.items():
            try:
                pkgs = sublime.load_settings(pkg_name + PREF_EXT)
                for key, val in pkg_prefs.items():
                    if isinstance(val, dict):
                        pkgs.set(key, pkgs.get(key).update(val))
                    elif val:
                        pkgs.set(key, val)
                    else:
                        pkgs.erase(key)
                sublime.save_settings(pkg_name + PREF_EXT)
            except:
                pass


class DeleteUserSkinCommand(sublime_plugin.WindowCommand):
    """Implements the 'delete_user_skin' command."""

    def is_visible(self):
        """Show command only if user skins exist."""
        return any(
            validate_skin(data) for data in decode_resource(
                "Packages/User/Saved Skins.skins").values())

    def run(self, name=None):
        """Delete a user defined skin or show quick panel to select one.

        Arguments:
            name (string): The name of the skin to delete.
        """
        skins = load_user_skins()
        if not skins:
            return

        def delete_skin(skin):
            """Delete the skin from 'Saved Skins.skins' file."""
            if skin not in skins.keys():
                sublime.status_message("Skin not deleted!")
                return
            del skins[skin]
            save_user_skins(skins)
            sublime.status_message("Skin %s deleted!" % skin)

        if name:
            return delete_skin(name)

        # the icon to display next to the skin name
        icon = "🚮 "
        # built quick panel items
        items = [[
            icon + skin,
            "Delete existing skin."
        ] for skin in sorted(skins.keys())]

        def on_done(index):
            """A quick panel item was selected."""
            if index >= 0:
                delete_skin(items[index][0].lstrip(icon))

        # display a quick panel with all user skins
        self.window.show_quick_panel(
            items=items, on_select=on_done,
            flags=sublime.KEEP_OPEN_ON_FOCUS_LOST)


class SaveUserSkinCommand(sublime_plugin.WindowCommand):
    """Implements the 'save_user_skin' command."""

    def run(self, name=None):
        """Save visual settings as user defined skin.

        If the command is called without arguments, it shows an input panel
        to ask the user for the desired name to save the skin as.

            sublime.run_command("save_user_skin")

        The command can be called to save the current skin
        with a predefined name:

            sublime.run_command("save_user_skin", {"name": "Preset 1"})

        Arguments:
            name (string): If not None this names the skin to save the current
                visual settings as.
        """
        skins = load_user_skins()

        def save_skin(name):
            """Save the skin with provided name."""

            # Compose the new skin by loading all settings from all existing
            # <pkg_name>.sublime-settings files defined in <template>.
            template = sublime.load_settings(PREF_SKIN).get("skin-template")
            new_skin = {}
            for pkg_name, css in template.items():
                val = self.transform(decode_resource(
                    "Packages/User/%s.sublime-settings" % pkg_name), css)
                if val:
                    new_skin[pkg_name] = val
            # Check whether the minimum requirements are met.
            if not validate_skin(new_skin):
                sublime.status_message("Invalid skin %s not saved!" % name)
                return
            # Save the skin.
            skins[name] = new_skin
            save_user_skins(skins)
            sublime.status_message("Saved skin %s!" % name)

        if name:
            return save_skin(name)

        # the icon to display next to the skin name
        icon = "🔃 "
        # built quick panel items
        items = [[
            "💾 Save as new skin ...",
            "Enter the name in the following input panel, please."
        ]] + [[
            icon + skin,
            "Update existing skin."
        ] for skin in sorted(skins.keys())]

        def on_done(index):
            """A quick panel item was selected."""
            if index == 0:
                # Save as new skin ...
                self.window.show_input_panel(
                    "Enter skins name:", "", save_skin, None, None)
            elif index > 0:
                # Update existing skin.
                save_skin(items[index][0].lstrip(icon))

        # display a quick panel with all user skins
        self.window.show_quick_panel(
            items=items, on_select=on_done,
            flags=sublime.KEEP_OPEN_ON_FOCUS_LOST)

    @classmethod
    def transform(cls, json, css):
        """Filter JSON object by a stylesheet.

        This function transforms the <json> object by recursively
        parsing it and returning only the child objects whose keys
        match the values in the cascaded stylesheet <css>.

        Arguments:
            json    The data source to filter
            css     The stylesheet used as filter

                    Each <object> must exist in <json>.
                    Each <key> and its value is read from <json> and
                    added to the returned object.

                    EXAMPLE:
                    <object> : [<key>, <key>, ...],
                    <object> : {
                        <object> : [<key>, <key>, ...]
                    }
        """
        if json and css:
            if isinstance(css, dict):
                node = {}
                for key, style in css.items():
                    value = cls.transform(json[key], style)
                    # do not add empty objects
                    if value:
                        node[key] = value
                return node
            if isinstance(css, list):
                return {key: json[key] for key in css if key in json}
            elif css in json:
                return {css: json[css]}
        return None
