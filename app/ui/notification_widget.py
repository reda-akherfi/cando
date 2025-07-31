"""
Notification widget for the Cando application.

This module provides a toast-style notification system that displays
non-intrusive notifications for success and error messages.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
)
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPainterPath


class NotificationWidget(QWidget):
    """
    Toast-style notification widget.

    Displays non-intrusive notifications that automatically fade out
    and can be manually dismissed.
    """

    def __init__(self, parent=None):
        """Initialize the notification widget."""
        super().__init__(parent)
        self.setup_ui()
        self.setup_animations()

        # Hide initially
        self.hide()

        # Auto-hide timer
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.timeout.connect(self.hide_notification)

    def setup_ui(self):
        """Set up the user interface."""
        self.setFixedSize(350, 80)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Content widget
        self.content_widget = QWidget()
        self.content_widget.setObjectName("notification-content")
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(15, 12, 15, 12)

        # Icon and text
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.icon_label)

        # Text layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)

        self.message_label = QLabel()
        self.message_label.setFont(QFont("Arial", 9))
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        text_layout.addWidget(self.message_label)

        content_layout.addLayout(text_layout)
        content_layout.addStretch()

        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.close_button.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.7);
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """
        )
        self.close_button.clicked.connect(self.hide_notification)
        content_layout.addWidget(self.close_button)

        layout.addWidget(self.content_widget)

        # Set default styling
        self.set_success_style()

    def setup_animations(self):
        """Set up fade in/out animations."""
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out_animation.finished.connect(self.hide)

    def set_success_style(self):
        """Set the success notification style (green)."""
        self.content_widget.setStyleSheet(
            """
            QWidget#notification-content {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 8px;
                border: 1px solid #4CAF50;
            }
        """
        )
        self.title_label.setStyleSheet("color: white;")
        self.icon_label.setText("✓")
        self.icon_label.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
        )

    def set_error_style(self):
        """Set the error notification style (red)."""
        self.content_widget.setStyleSheet(
            """
            QWidget#notification-content {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f44336, stop:1 #d32f2f);
                border-radius: 8px;
                border: 1px solid #f44336;
            }
        """
        )
        self.title_label.setStyleSheet("color: white;")
        self.icon_label.setText("✗")
        self.icon_label.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
        )

    def show_success(self, title: str, message: str = "", duration: int = 4000):
        """Show a success notification."""
        self.set_success_style()
        self.show_notification(title, message, duration)

    def show_error(self, title: str, message: str = "", duration: int = 5000):
        """Show an error notification."""
        self.set_error_style()
        self.show_notification(title, message, duration)

    def show_notification(self, title: str, message: str = "", duration: int = 4000):
        """Show a notification with the given title and message."""
        self.title_label.setText(title)
        self.message_label.setText(message)
        self.message_label.setVisible(bool(message))

        # Position the notification
        self.position_notification()

        # Show with animation
        self.show()
        self.fade_in_animation.start()

        # Auto-hide after duration
        if duration > 0:
            self.auto_hide_timer.start(duration)

    def position_notification(self):
        """Position the notification in the top-right corner of the parent window."""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + parent_rect.width() - self.width() - 20
            y = parent_rect.y() + 20
            self.move(x, y)
        else:
            # Fallback to screen positioning
            from PySide6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            x = screen.width() - self.width() - 20
            y = 20
            self.move(x, y)

    def hide_notification(self):
        """Hide the notification with fade out animation."""
        self.auto_hide_timer.stop()
        self.fade_out_animation.start()

    def paintEvent(self, event):
        """Custom paint event for rounded corners and shadow."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create shadow effect
        shadow_color = QColor(0, 0, 0, 30)
        for i in range(8):
            shadow_color.setAlpha(30 - i * 3)
            painter.setPen(Qt.NoPen)
            painter.setBrush(shadow_color)
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 8, 8)


class NotificationManager:
    """
    Manager for handling multiple notifications.

    Provides a centralized way to show notifications and manages
    notification stacking and positioning.
    """

    def __init__(self, parent=None):
        """Initialize the notification manager."""
        self.parent = parent
        self.notifications = []
        self.max_notifications = 3
        self.notification_spacing = 10

    def show_success(self, title: str, message: str = "", duration: int = 4000):
        """Show a success notification."""
        self._show_notification("success", title, message, duration)

    def show_error(self, title: str, message: str = "", duration: int = 5000):
        """Show an error notification."""
        self._show_notification("error", title, message, duration)

    def _show_notification(
        self, notification_type: str, title: str, message: str, duration: int
    ):
        """Show a notification of the specified type."""
        # Create new notification
        notification = NotificationWidget(self.parent)

        # Connect to removal signal
        notification.fade_out_animation.finished.connect(
            lambda: self._remove_notification(notification)
        )

        # Show notification
        if notification_type == "success":
            notification.show_success(title, message, duration)
        else:
            notification.show_error(title, message, duration)

        # Add to list
        self.notifications.append(notification)

        # Reposition all notifications
        self._reposition_notifications()

        # Remove oldest if too many
        if len(self.notifications) > self.max_notifications:
            oldest = self.notifications.pop(0)
            oldest.hide_notification()

    def _remove_notification(self, notification: NotificationWidget):
        """Remove a notification from the list."""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.deleteLater()
            self._reposition_notifications()

    def _reposition_notifications(self):
        """Reposition all active notifications."""
        y_offset = 20
        for notification in self.notifications:
            if notification.parent():
                parent_rect = notification.parent().geometry()
                x = parent_rect.x() + parent_rect.width() - notification.width() - 20
                y = parent_rect.y() + y_offset
                notification.move(x, y)
                y_offset += notification.height() + self.notification_spacing
            else:
                # Fallback to screen positioning
                from PySide6.QtWidgets import QApplication

                screen = QApplication.primaryScreen().geometry()
                x = screen.width() - notification.width() - 20
                y = y_offset
                notification.move(x, y)
                y_offset += notification.height() + self.notification_spacing
