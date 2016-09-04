import sublime
import sublime_plugin
import os
import json

def absolute_user_path():
    """
    Return absolute path of the Packages/User
    """
    return sublime.packages_path() + os.sep + "User" + os.sep

def is_skin_valid(skin_data):
    """
    For a skin to be valid at least "color_scheme" and "theme" must exist!

    args:
        skin_data - JSON object with all settings to apply for the skin.
    """
    try:
        for key in ["color_scheme", "theme"]:
            if not any(sublime.find_resources(os.path.basename(skin_data["Preferences"][key]))):
                return False
        return True
    except:
        return False

def load_skin(pkg_name, skin_name):
    """
    Load a single skin from a Packages/<pkg_name>/*.skins

    args:
        pkg_name    - the package name to look for skin files in.
        skin_name   - the name of the skin whose data to load.

    returns:
        skin    - tuble with all skin information
                  skin[0] = package name
                  skin[1] = skin name
                  skin[2] = skin data
    """
    for skins_file in sublime.find_resources("*.skins"):
        if pkg_name in skins_file:
            data = sublime.decode_value(sublime.load_resource(skins_file))[skin_name]
            if is_skin_valid(data):
                return [pkg_name, skin_name, data]

    return None

def load_skins():
    """
    Generate a list of all valid skins from all packages.
    Each skin is a tuble with following fields
      skin[0] = package name
      skin[1] = skin name
      skin[2] = skin data
    """
    for skins_file in sublime.find_resources("*.skins"):
        try:
            pkg_name = skins_file.split("/")[1]
            for skin_name, data in sublime.decode_value(sublime.load_resource(skins_file)).items():
                if is_skin_valid(data):
                    yield [pkg_name, skin_name, data]

        except:
            sublime.status_message("Parse error in " + skins_file)

    return None

def load_user_skins():
    """
    Open the "Saved Skins.skins" and read all valid skins from it.
    """
    try:
        return { name : data
            for name, data in sublime.decode_value(
                sublime.load_resource("Packages/User/Saved Skins.skins")).items()
            if is_skin_valid(data) }

    except:
        return {}

def save_user_skins(skins):
    """
    Save the skins to the "Saved Skins.skins".
    """
    with open(absolute_user_path() + "Saved Skins.skins", "w") as f:
        f.write(sublime.encode_value(skins, True))


class SetSkinCommand(sublime_plugin.WindowCommand):

    def __init__(self, window):
        self.window = window
        self.changeset = {}
        self.settings = sublime.load_settings("Preferences.sublime-settings")

    def run(self, package = None, name = None):
        """
        API entry point for command "set_skin"

        If "set_skin" is called with both args "package" and "name", the provided
        information will be used to directly switch to the desired skin.

        If at least one of the args is None, a quick panel with all available skins
        is displayed.

        args:
            package   - name of the package providing the skin or (User)
            name      - name of the skin in the <skins>.skins file
        """

        if package and name:
            try:
                self.apply_settings(load_skin(package, name))
            except:
                sublime.status_message("Can't switch to invalid skin!")
        else:
            current_skin = self.settings.get("skin")
            selected_index = -1
            idx = 0

            skins = []
            for pkg, name, data in load_skins():
                skins.append([pkg, name, data])
                if current_skin == pkg + "/" + name:
                    selected_index = idx
                idx += 1

            self.changeset = {}
            self.window.show_quick_panel(
                items = [ [ skin[1], skin[0] ] for skin in skins ],
                selected_index = selected_index,
                on_select = lambda x: self.on_select(skins[x], x < 0),
                on_highlight = lambda x: self.on_highlight(skins[x]))


    def on_select(self, skin, abort):
        """
        On select event handler for quick panel.

        args:
            skin    - tuble with all skin information
                      skin[0] = package name
                      skin[1] = skin name
                      skin[2] = skin data
            abort   - TRUE to restore old settings.
        """
        if abort:
            for key, val in self.changeset.items():
                if val:
                    self.settings.set(key, val)
                else:
                    self.settings.erase(key)

            sublime.save_settings("Preferences.sublime-settings")

        else:
            self.apply_settings(skin)

    def on_highlight(self, skin):
        """
        Preview the theme and color scheme as soon as a skin is highlighted.

        args:
            skin    - tuble with all skin information
                      skin[0] = package name
                      skin[1] = skin name
                      skin[2] = skin data
        """
        for key, val in skin[2]["Preferences"].items():
            # backup settings before changing the first time
            if not key in self.changeset:
                self.changeset[key] = self.settings.get(key)

            if val:
                self.settings.set(key, val)
            else:
                self.settings.erase(key)

    def apply_settings(self, skin):
        """
        Apply all settings

        args:
            skin    - tuble with all skin information
                      skin[0] = package name
                      skin[1] = skin name
                      skin[2] = skin data
        """
        self.settings.set("skin", skin[0] + "/" + skin[1])
        for pkg_name, skns in skin[2].items():
            try:
                pkgs = sublime.load_settings(pkg_name + ".sublime-settings")
                for key, val in skns.items():
                    if type(val) is dict:
                        pkgs.set(key, pkgs.get(key).update(val))
                    elif val:
                        pkgs.set(key, val)
                    else:
                        pkgs.erase(key)
                sublime.save_settings(pkg_name + ".sublime-settings")
            except:
                pass


class DeleteUserSkinCommand(sublime_plugin.WindowCommand):

    def run(self, name = None):
        skins = load_user_skins()
        if name:
            self.delete(skins, name)
        else:
            self.window.show_quick_panel(
                items = [ [ skin, "User" ] for skin in sorted(skins.keys()) ],
                on_select = lambda x: self.delete(skins, sorted(skins.keys())[x], x < 0))

    @staticmethod
    def delete(skins, skin, abort = False):
        if not abort and skin in skins.keys():
            del skins[skin]
            save_user_skins(skins)
            sublime.status_message("Skin " + skin + " deleted!")
        else:
            sublime.status_message("Skin not deleted!")


class SaveUserSkinCommand(sublime_plugin.WindowCommand):

    def run(self, name = None):
        if name:
            template = sublime.load_settings("Skins.sublime-settings").get("skin-template")
            skins = load_user_skins()
            # BUG: sublime.load_setting(...) does not work reliably here, I don't know why.
            #      cascaded settings are sometimes read as Null-Value, so use JSON library.
            skin = {}
            for pkg, css in template.items():
                with open(absolute_user_path() + pkg + ".sublime-settings") as f:
                    pkgs = self.transform(json.load(f), css)
                    if pkgs:
                       skin[pkg] = pkgs

            skins[name] = skin
            save_user_skins(skins)
            sublime.status_message("Saved skin " + name)
        else:
            self.window.show_input_panel("Enter skins name:", "",
                                         self.run, None, None)

    def transform(self, json, css):
        """
        Filter JSON object by a Style-Sheet

        This function transforms the <json> object by recursivly
        parsing it and returning only the child objects whose keys
        match the values in the cascaded stylesheed <css>.

        args:
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
            if type(css) is dict:
                node = {}
                for key, ss in css.items():
                    value = self.transform(json[key], ss)
                    # do not add empty objects
                    if value:
                        node[key] = value
                return node

            if type(css) is list:
                return { key : json[key] for key in css if key in json }

            elif css in json:
                return { css : json[css] }

        return None
