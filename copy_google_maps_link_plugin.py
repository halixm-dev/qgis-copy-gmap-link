# Import necessary QGIS and Qt modules
# from qgis.PyQt.QtCore import QCoreApplication # Not directly used
# from qgis.PyQt.QtGui import QIcon # Not used
from qgis.PyQt.QtWidgets import QAction, QApplication, QMenu
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsMessageLog, Qgis
import sip # Import sip to check if Qt objects have been deleted

# This is a common way to store a reference to the QGIS interface
iface = None

# Global variable to store the clicked point
clicked_point_canvas_crs = None

def plugin_path():
    """Helper function to get the plugin's directory (optional, but good practice for icons etc.)"""
    import os
    return os.path.dirname(os.path.realpath(__file__))

class CopyGoogleMapsLinkPlugin:
    """
    This class defines the QGIS plugin.
    """
    def __init__(self, qgis_iface):
        """
        Constructor.

        :param qgis_iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS application.
        """
        global iface
        iface = qgis_iface
        self.plugin_name = "Copy Google Maps Link"
        self.canvas = iface.mapCanvas()

        # Create the QAction once and parent it to the canvas for stability.
        # The canvas is a QObject that persists, so the action won't be prematurely deleted
        # before the canvas itself is handled.
        self.context_menu_action = QAction("Copy Google Maps Link Here", self.canvas)
        self.context_menu_action.triggered.connect(self.copy_google_maps_link_from_context)

        QgsMessageLog.logMessage(f"{self.plugin_name}: __init__ completed. Action created.", self.plugin_name, Qgis.Info)


    def initGui(self):
        """
        This method is called when the plugin is loaded into QGIS.
        It's used to set up GUI interactions, like connecting signals.
        """
        # Connect to the canvas's contextMenuAboutToShow signal.
        # This signal is emitted just before the context menu is shown, allowing
        # us to add our custom action to it.
        self.canvas.contextMenuAboutToShow.connect(self.prepare_canvas_context_menu)

        QgsMessageLog.logMessage(f"{self.plugin_name}: initGui completed and signal connected.", self.plugin_name, Qgis.Info)


    def prepare_canvas_context_menu(self, menu, event):
        """
        Called when the map canvas context menu is about to be shown.
        We add our persistent action to the menu here.
        'menu' is the QMenu object for the context menu.
        'event' is a QgsMapMouseEvent which contains the clicked point.
        """
        global clicked_point_canvas_crs
        if event and event.mapPoint(): # Ensure event and mapPoint are valid
            # Store the clicked point in the map's current Coordinate Reference System (CRS)
            clicked_point_canvas_crs = QgsPointXY(event.mapPoint())
            # QgsMessageLog.logMessage(f"Clicked point (Canvas CRS): {clicked_point_canvas_crs.toString()}", self.plugin_name, Qgis.Info)

            # Add our pre-existing action to the menu.
            # No need to create or re-parent it here as it's managed by the plugin instance
            # and parented to the canvas.
            menu.addSeparator()
            menu.addAction(self.context_menu_action)
            # QgsMessageLog.logMessage(f"{self.plugin_name}: Action added to context menu.", self.plugin_name, Qgis.Info)
        else:
            QgsMessageLog.logMessage(f"{self.plugin_name}: prepare_canvas_context_menu called without a valid event or mapPoint.", self.plugin_name, Qgis.Warning)


    def copy_google_maps_link_from_context(self):
        """
        This function is called when the context menu action is triggered.
        It uses the globally stored clicked_point_canvas_crs.
        """
        global clicked_point_canvas_crs
        if not clicked_point_canvas_crs:
            iface.messageBar().pushMessage("Error", "Could not get clicked point. Please right-click on the map again.", level=Qgis.Critical, duration=4)
            QgsMessageLog.logMessage("copy_google_maps_link_from_context: clicked_point_canvas_crs is None.", self.plugin_name, Qgis.Warning)
            return

        try:
            # Get the current map canvas Coordinate Reference System (CRS)
            canvas_crs = self.canvas.mapSettings().destinationCrs()
            if not canvas_crs.isValid():
                iface.messageBar().pushMessage("Error", "Invalid Canvas CRS. Cannot perform transformation.", level=Qgis.Critical, duration=5)
                QgsMessageLog.logMessage(f"Invalid Canvas CRS: {canvas_crs.authid()}", self.plugin_name, Qgis.Critical)
                clicked_point_canvas_crs = None # Clear invalid point state
                return

            # Define the target CRS (WGS 84 for Google Maps)
            target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            if not target_crs.isValid():
                iface.messageBar().pushMessage("Error", "Could not define target CRS (EPSG:4326).", level=Qgis.Critical, duration=5)
                QgsMessageLog.logMessage("Failed to initialize EPSG:4326.", self.plugin_name, Qgis.Critical)
                clicked_point_canvas_crs = None # Clear invalid point state
                return

            # Create a coordinate transformation object
            transform = QgsCoordinateTransform(canvas_crs, target_crs, QgsProject.instance())

            # Transform the point from the canvas CRS to WGS 84
            point_wgs84 = transform.transform(clicked_point_canvas_crs)

            # Check if transformation was successful and coordinates are valid
            if not (point_wgs84.x() == point_wgs84.x() and point_wgs84.y() == point_wgs84.y()) or \
               abs(point_wgs84.x()) == float('inf') or abs(point_wgs84.y()) == float('inf') or \
               not (-90 <= point_wgs84.y() <= 90 and -180 <= point_wgs84.x() <= 180):
                 iface.messageBar().pushMessage("Error", "Coordinate transformation failed or resulted in invalid WGS84 coordinates. Check project CRS.", level=Qgis.Critical, duration=5)
                 QgsMessageLog.logMessage(f"Coordinate transformation resulted in invalid WGS84. Original: {clicked_point_canvas_crs.toString()}, Canvas CRS: {canvas_crs.authid()}, Transformed: {point_wgs84.toString()}", self.plugin_name, Qgis.Critical)
                 clicked_point_canvas_crs = None
                 return

            # Create the Google Maps link (lat,lon format)
            google_maps_link = f"https://www.google.com/maps?q={point_wgs84.y()},{point_wgs84.x()}"

            # Copy the generated link to the system clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(google_maps_link)

            iface.messageBar().pushMessage("Success", f"Google Maps link copied: {google_maps_link}", level=Qgis.Success, duration=5)
            # QgsMessageLog.logMessage(f"Copied link: {google_maps_link}", self.plugin_name, Qgis.Info)

        except Exception as e:
            error_message = f"Error copying Google Maps link: {str(e)}"
            iface.messageBar().pushMessage("Error", error_message, level=Qgis.Critical, duration=5)
            QgsMessageLog.logMessage(error_message, self.plugin_name, Qgis.Critical)
        finally:
            # Clear the globally stored clicked point after use.
            clicked_point_canvas_crs = None


    def unload(self):
        """
        This method is called when the plugin is unloaded from QGIS.
        It's used to clean up resources, such as disconnecting signals
        and deleting objects created by the plugin.
        """
        # Disconnect the signal connected in initGui
        try:
            if self.canvas: # Ensure canvas object still exists
                self.canvas.contextMenuAboutToShow.disconnect(self.prepare_canvas_context_menu)
                QgsMessageLog.logMessage(f"{self.plugin_name}: Disconnected from contextMenuAboutToShow.", self.plugin_name, Qgis.Info)
        except TypeError: # Can occur if it was never connected or already disconnected
            QgsMessageLog.logMessage(f"{self.plugin_name}: Signal (contextMenuAboutToShow) was already disconnected or not connected.", self.plugin_name, Qgis.Warning)
        except Exception as e: # Catch any other unexpected errors
            QgsMessageLog.logMessage(f"Error disconnecting signal in unload: {str(e)}", self.plugin_name, Qgis.Warning)

        # Clean up the QAction
        if self.context_menu_action:
            # Check if the underlying C++ object for the QAction still exists before calling deleteLater.
            # This prevents a RuntimeError if it has already been deleted (e.g., by its parent canvas).
            if not sip.isdeleted(self.context_menu_action):
                self.context_menu_action.deleteLater()
                QgsMessageLog.logMessage(f"{self.plugin_name}: Context menu action scheduled for deletion.", self.plugin_name, Qgis.Info)
            else:
                QgsMessageLog.logMessage(f"{self.plugin_name}: Context menu action was already deleted (likely by parent).", self.plugin_name, Qgis.Info)
            self.context_menu_action = None # Clear the Python reference

        QgsMessageLog.logMessage(f"{self.plugin_name}: Unloaded successfully.", self.plugin_name, Qgis.Info)


# Standard QGIS plugin functions:

def classFactory(iface_obj):
    global iface
    iface = iface_obj
    return CopyGoogleMapsLinkPlugin(iface_obj)

def name():
    return "Copy Google Maps Link"

def description():
    return "Right-click on the map canvas to copy a Google Maps link for the clicked location."

def version():
    return "0.2.4" # Incremented version due to fix for RuntimeError on unload

def qgisMinimumVersion():
    return "3.0"

def authorName():
    return "AI Assistant (with user feedback)"

def icon():
    # import os # Uncomment if using plugin_path() for an icon
    # return os.path.join(plugin_path(), "icon.png") # Example
    return ""

def about():
    return """
    This plugin adds an option to the map canvas context menu to copy a Google Maps link
    for the clicked geographic coordinates. The coordinates are transformed to WGS84 (EPSG:4326).
    Version: 0.2.4
    """

def category():
    return "Map Tools"

def type():
    return Qgis.PluginType.UI
