# -*- coding: utf-8 -*-

def classFactory(iface):
    """
    Load the plugin class from the main plugin file.
    This function is called by QGIS when the plugin is loaded.
    """
    # Import the main plugin class
    from .copy_google_maps_link_plugin import CopyGoogleMapsLinkPlugin
    return CopyGoogleMapsLinkPlugin(iface)

# You can also define other plugin metadata functions here if you prefer,
# but it's common to keep them in the main plugin file or metadata.txt.
# For example:
# def name():
#     return "Copy Google Maps Link Plugin"
#
# def description():
#     return "Right-click on map to copy Google Maps link."
#
# def version():
#     return "0.1"
#
# etc.
