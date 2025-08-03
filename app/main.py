"""
Main entry point for the Cando application.

This module launches the Cando productivity desktop application using PySide6.
It initializes the main window and starts the Qt event loop.
"""

import sys
import os
import logging
from datetime import datetime
from PySide6.QtWidgets import QApplication
from app.views.main_window import MainWindow
from app.services.database import DatabaseService
from app.services.analytics import AnalyticsService
from app.services.data_init import DataInitializer
from app.controllers.timer_controller import TimerController
from app.ui.theme import DarkTheme


def setup_logging():
    """Setup logging to file in the same directory as the executable."""
    try:
        # Get the directory where the executable is located
        if getattr(sys, "frozen", False):
            # Running as compiled executable
            exe_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            exe_dir = os.path.dirname(os.path.abspath(__file__))

        # Create log file path
        log_file = os.path.join(exe_dir, "Cando.log")

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, mode="a", encoding="utf-8"),
                logging.StreamHandler(sys.stdout),  # Also log to console if available
            ],
        )

        logging.info("=" * 50)
        logging.info("Cando Application Started")
        logging.info(f"Log file: {log_file}")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Executable directory: {exe_dir}")

    except Exception as e:
        # Fallback: try to log to current directory
        try:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.FileHandler("Cando.log", mode="a", encoding="utf-8")],
            )
            logging.error(f"Failed to setup logging properly: {e}")
        except:
            pass  # If all else fails, just continue without logging


def main():
    """
    Main entry point for the Cando application.

    Initializes the Qt application, creates the main window,
    and starts the event loop.
    """
    # Setup logging first
    setup_logging()

    try:
        logging.info("Initializing Qt application...")
        app = QApplication(sys.argv)

        # Apply dark theme to the entire application
        # DarkTheme.apply_to_application(app)

        logging.info("Initializing database and services...")
        # Initialize database and services
        db_service = DatabaseService()
        analytics_service = AnalyticsService(db_service)
        timer_controller = TimerController(db_service)
        data_initializer = DataInitializer(db_service)

        # Initialize default configuration only (no sample data)
        if data_initializer.is_database_empty():
            logging.info("Initializing default configuration...")
            data_initializer.initialize_default_config()

        logging.info("Creating main window...")
        # Create main window with services
        window = MainWindow(db_service, analytics_service, timer_controller)

        # Check if window should be maximized
        always_maximized = (
            db_service.get_config("always_maximized", "true").lower() == "true"
        )
        if always_maximized:
            window.showMaximized()
            logging.info("Window shown maximized")
        else:
            window.show()
            logging.info("Window shown normally")

        logging.info("Starting Qt event loop...")
        sys.exit(app.exec())

    except Exception as e:
        logging.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
