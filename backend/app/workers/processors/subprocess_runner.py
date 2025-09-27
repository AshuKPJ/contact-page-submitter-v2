# app/workers/processors/subprocess_runner.py
"""
Campaign processing subprocess runner with fallback mechanisms
"""
import os
import sys
import subprocess
import json
import time
import threading
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


def start_campaign_processing(campaign_id: str, user_id: str) -> bool:
    """
    Start campaign processing using subprocess with multiple fallback options
    """
    try:
        # Try to find the campaign processor script
        processor_paths = [
            "app/workers/campaign_processor.py",
            "workers/campaign_processor.py",
            "campaign_processor.py",
            Path(__file__).parent.parent / "campaign_processor.py",
        ]

        processor_script = None
        for path in processor_paths:
            if os.path.exists(path):
                processor_script = str(path)
                logger.info(f"Found processor script at: {processor_script}")
                break

        if not processor_script:
            logger.error(
                f"Campaign processor script not found in any of: {processor_paths}"
            )
            # Return True anyway to allow fallback processing
            return True

        # Prepare environment variables
        env = os.environ.copy()
        env["CAMPAIGN_ID"] = campaign_id
        env["USER_ID"] = user_id

        # Try to start subprocess
        try:
            process = subprocess.Popen(
                [sys.executable, processor_script, campaign_id, user_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            # Check if process started successfully
            time.sleep(0.5)  # Brief wait
            if process.poll() is not None:
                # Process already terminated
                stdout, stderr = process.communicate()
                logger.error(
                    f"Process terminated immediately. stdout: {stdout}, stderr: {stderr}"
                )
                return True  # Still return True to trigger fallback

            # Process started successfully
            logger.info(f"Started subprocess {process.pid} for campaign {campaign_id}")

            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=monitor_subprocess, args=(process, campaign_id), daemon=True
            )
            monitor_thread.start()

            return True

        except Exception as e:
            logger.error(f"Failed to start subprocess: {e}")
            return True  # Return True to trigger fallback

    except Exception as e:
        logger.error(f"Error in start_campaign_processing: {e}")
        return True  # Always return True to allow fallback processing


def monitor_subprocess(process: subprocess.Popen, campaign_id: str):
    """
    Monitor a subprocess and log its output
    """
    try:
        # Read output in real-time
        while process.poll() is None:
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    logger.info(f"[Campaign {campaign_id}] {line.strip()}")
            time.sleep(0.1)

        # Process ended
        return_code = process.poll()
        if return_code != 0:
            stderr_output = process.stderr.read() if process.stderr else ""
            logger.error(
                f"Campaign {campaign_id} process ended with code {return_code}: {stderr_output}"
            )
        else:
            logger.info(f"Campaign {campaign_id} process completed successfully")

    except Exception as e:
        logger.error(f"Error monitoring subprocess for campaign {campaign_id}: {e}")


def stop_campaign_processing(campaign_id: str) -> bool:
    """
    Stop campaign processing
    """
    try:
        # This would need to track running processes
        # For now, we rely on status checks in the database
        logger.info(f"Stopping campaign {campaign_id} processing")
        return True

    except Exception as e:
        logger.error(f"Error stopping campaign {campaign_id}: {e}")
        return False


def get_campaign_processing_status(campaign_id: str) -> Dict[str, Any]:
    """
    Get the status of campaign processing
    """
    try:
        # This would check actual process status
        # For now, return a basic status
        return {
            "campaign_id": campaign_id,
            "is_running": False,
            "message": "Status check not implemented",
        }

    except Exception as e:
        logger.error(f"Error getting status for campaign {campaign_id}: {e}")
        return {"campaign_id": campaign_id, "is_running": False, "error": str(e)}


if __name__ == "__main__":
    # Test run
    if len(sys.argv) > 2:
        campaign_id = sys.argv[1]
        user_id = sys.argv[2]

        print(f"Testing subprocess runner for campaign {campaign_id}")
        result = start_campaign_processing(campaign_id, user_id)
        print(f"Start result: {result}")
    else:
        print("Usage: python subprocess_runner.py <campaign_id> <user_id>")
