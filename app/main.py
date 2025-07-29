"""
Main entry point for the Cando application.

This module launches the Cando productivity desktop application using PySide6.
It initializes the main window and starts the Qt event loop.
"""

import sys
from PySide6.QtWidgets import QApplication
from app.views.main_window import MainWindow
from app.services.database import DatabaseService
from app.services.analytics import AnalyticsService
from app.services.data_init import DataInitializer
from app.controllers.timer_controller import TimerController


def main():
    """
    Main entry point for the Cando application.

    Initializes the Qt application, creates the main window,
    and starts the event loop.
    """
    app = QApplication(sys.argv)

    # Initialize database and services
    db_service = DatabaseService()
    analytics_service = AnalyticsService(db_service)
    timer_controller = TimerController(db_service)
    data_initializer = DataInitializer(db_service)

    # Initialize sample data if database is empty
    if data_initializer.is_database_empty():
        print("Initializing sample data...")
        data_initializer.initialize_sample_data()

    # Create main window with services
    window = MainWindow(db_service, analytics_service, timer_controller)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
