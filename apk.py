from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import win32clipboard
import zlib
import math

class CopyNotifier(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.text = "Copied"
        self.font = QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold)  # Väčší font
        self.setWindowFlags(
            QtCore.Qt.Tool
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.X11BypassWindowManagerHint
            | QtCore.Qt.WindowDoesNotAcceptFocus  # Skrytie v taskbare
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Počiatočná veľkosť pre loading (bodky)
        self.setFixedSize(100, 60)

        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        screen_geometry = QtWidgets.QApplication.primaryScreen().geometry()
        self.center_x = (screen_geometry.width() - self.width()) // 2
        self.bottom_y = screen_geometry.height() + 10
        self.top_y = screen_geometry.height() - self.height() - 40

        self.move(self.center_x, self.bottom_y)

        self.anim_duration = 300  # ms
        self.transition_duration = 400  # ms pre prechod
        self.dot_phase = 0
        self.checkmark_progress = 0
        self.dots_opacity = 1.0
        self.checkmark_opacity = 0.0

        self.pos_anim = QtCore.QPropertyAnimation(self, b"pos", self)
        self.pos_anim.setDuration(self.anim_duration)
        self.pos_anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.opacity_anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.opacity_anim.setDuration(self.anim_duration)
        self.opacity_anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.size_anim = QtCore.QPropertyAnimation(self, b"size", self)
        self.size_anim.setDuration(self.transition_duration)
        self.size_anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.state = "loading"
        self.pos_anim.finished.connect(self.on_pos_anim_finished)

        # Timer for smooth dots animation
        self.dots_timer = QtCore.QTimer(self)
        self.dots_timer.timeout.connect(self.update_dots)
        self.dots_timer.start(16)  # ~60 FPS (1000ms / 60 ≈ 16ms)

        # Start loading animation
        self.show()
        self.start_loading_animation()

    def update_dots(self):
        if self.state == "loading":
            self.dot_phase = (self.dot_phase + 0.1) % (2 * math.pi)  # Rýchlosť skákania
            self.update()
        elif self.state == "transition":
            self.dots_opacity = max(self.dots_opacity - 0.025, 0.0)
            self.checkmark_opacity = min(self.checkmark_opacity + 0.025, 1.0)
            self.checkmark_progress = min(self.checkmark_progress + 0.05, 1.0)
            if self.checkmark_opacity >= 1.0 and self.dots_opacity <= 0.0:
                self.state = "checkmark"
                self.dots_timer.stop()
                QtCore.QTimer.singleShot(1000, self.start_closing)
            self.update()

    def start_loading_animation(self):
        self.state = "loading"
        self.setFixedSize(100, 60)  # Box pre bodky
        self.center_x = (QtWidgets.QApplication.primaryScreen().geometry().width() - self.width()) // 2
        self.bottom_y = QtWidgets.QApplication.primaryScreen().geometry().height() + 10
        self.top_y = QtWidgets.QApplication.primaryScreen().geometry().height() - self.height() - 40
        self.move(self.center_x, self.bottom_y)
        self.dot_phase = 0
        self.dots_opacity = 1.0
        self.checkmark_opacity = 0.0
        self.checkmark_progress = 0.0
        self.opacity_effect.setOpacity(0)

        self.pos_anim.setStartValue(QtCore.QPoint(self.center_x, self.bottom_y))
        self.pos_anim.setEndValue(QtCore.QPoint(self.center_x, self.top_y))
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)

        self.pos_anim.start()
        self.opacity_anim.start()
        QtCore.QTimer.singleShot(2000, self.start_transition)

    def start_transition(self):
        if self.state != "loading":
            return
        self.state = "transition"
        self.size_anim.setStartValue(QtCore.QSize(100, 60))
        self.size_anim.setEndValue(QtCore.QSize(80, 60))
        self.size_anim.start()

    def start_closing(self):
        if self.state != "checkmark":
            return
        self.state = "closing"

        self.pos_anim.setStartValue(QtCore.QPoint(self.center_x, self.top_y))
        self.pos_anim.setEndValue(QtCore.QPoint(self.center_x, self.bottom_y))
        self.opacity_anim.setStartValue(1)
        self.opacity_anim.setEndValue(0)

        self.pos_anim.start()
        self.opacity_anim.start()

    def show_notification(self):
        if self.state != "hidden":
            return

        self.state = "showing"
        # Box pre text "Copied"
        metrics = QtGui.QFontMetrics(self.font)
        text_width = metrics.horizontalAdvance(self.text) + 24  # Väčší padding
        text_height = metrics.height() + 24  # Väčší padding
        self.setFixedSize(text_width, text_height)
        self.center_x = (QtWidgets.QApplication.primaryScreen().geometry().width() - self.width()) // 2
        self.bottom_y = QtWidgets.QApplication.primaryScreen().geometry().height() + 10
        self.top_y = QtWidgets.QApplication.primaryScreen().geometry().height() - self.height() - 40
        self.move(self.center_x, self.bottom_y)
        self.show()

        self.pos_anim.setStartValue(QtCore.QPoint(self.center_x, self.bottom_y))
        self.pos_anim.setEndValue(QtCore.QPoint(self.center_x, self.top_y))

        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)

        self.pos_anim.start()
        self.opacity_anim.start()

    def on_pos_anim_finished(self):
        if self.state == "showing":
            self.state = "visible"
            QtCore.QTimer.singleShot(600, self.start_hiding)
        elif self.state == "hiding":
            self.state = "hidden"
            self.hide()
        elif self.state == "loading":
            self.state = "loading"
        elif self.state == "closing":
            self.state = "hidden"
            self.hide()

    def start_hiding(self):
        if self.state != "visible":
            return
        self.state = "hiding"

        self.pos_anim.setStartValue(QtCore.QPoint(self.center_x, self.top_y))
        self.pos_anim.setEndValue(QtCore.QPoint(self.center_x, self.bottom_y))

        self.opacity_anim.setStartValue(1)
        self.opacity_anim.setEndValue(0)

        self.pos_anim.start()
        self.opacity_anim.start()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(rect), 10, 10)
        painter.fillPath(path, QtGui.QColor(0, 0, 0, 230))

        if self.state in ["loading", "transition", "checkmark", "closing"]:
            center_x = rect.width() / 2
            center_y = rect.height() / 2
            dot_radius = 4
            spacing = 12

            # Draw jumping dots only if dots_opacity > 0
            if self.state in ["loading", "transition"] and self.dots_opacity > 0:
                painter.setOpacity(self.dots_opacity)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QtGui.QColor(255, 255, 255))
                for i in range(3):
                    offset = math.sin(self.dot_phase + i * (2 * math.pi / 3)) * 4
                    x = center_x + (i - 1) * spacing
                    y = center_y - offset
                    painter.drawEllipse(QtCore.QPointF(x, y), dot_radius, dot_radius)

            # Draw checkmark only if checkmark_opacity > 0
            if self.state in ["transition", "checkmark", "closing"] and self.checkmark_opacity > 0:
                painter.setOpacity(self.checkmark_opacity)
                painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0), 5))
                checkmark_path = QtGui.QPainterPath()
                checkmark_path.moveTo(center_x - 15, center_y)
                checkmark_path.lineTo(center_x - 5, center_y + 10)
                checkmark_path.lineTo(center_x + 15, center_y - 10)
                total_length = checkmark_path.length()
                if self.checkmark_progress < 1.0:
                    end_percent = checkmark_path.percentAtLength(total_length * self.checkmark_progress)
                    sub_path = QtGui.QPainterPath()
                    sub_path.moveTo(checkmark_path.pointAtPercent(0))
                    for t in range(1, int(end_percent * 100) + 1):
                        sub_path.lineTo(checkmark_path.pointAtPercent(t / 100.0))
                    painter.drawPath(sub_path)
                else:
                    painter.drawPath(checkmark_path)

        else:
            painter.setFont(self.font)
            painter.setPen(QtGui.QColor(255, 255, 255))
            metrics = QtGui.QFontMetrics(self.font)
            text_width = metrics.horizontalAdvance(self.text)
            text_height = metrics.height()
            x = (rect.width() - text_width) / 2
            y = (rect.height() + text_height) / 2 - metrics.descent()
            painter.drawText(int(x), int(y), self.text)

class ClipboardMonitor(QtCore.QThread):
    new_copy = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.last_hash = None

    def run(self):
        while self.running:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                    paths = sorted(list(data))
                    joined = '|'.join(paths)
                    current_hash = zlib.crc32(joined.encode())
                elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    current_hash = zlib.crc32(text.encode())
                elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT).decode('utf-8', errors='ignore')
                    current_hash = zlib.crc32(text.encode())
                else:
                    current_hash = None
            except:
                current_hash = None
            finally:
                win32clipboard.CloseClipboard()

            if current_hash is not None and current_hash != self.last_hash:
                self.last_hash = current_hash
                self.new_copy.emit()

            self.msleep(100)

def main():
    app = QtWidgets.QApplication(sys.argv)
    notifier = CopyNotifier()
    monitor = ClipboardMonitor()
    monitor.new_copy.connect(notifier.show_notification)
    monitor.start()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()