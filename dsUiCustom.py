from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Qt

# PYSIDE_DESIGNER_PLUGINS
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

class scentSlider(QSlider):
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            e.accept()
            x = e.pos().x()
            value = (self.maximum() - self.minimum()) * x / self.width() + self.minimum()
            self.setValue(value)
        else:
            return super().mousePressEvent(e)


















