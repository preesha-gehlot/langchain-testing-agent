import logging
from datetime import datetime
from typing import Any
import json
import sys
import os

# Configure logging for Google Cloud Run
def setup_logging(name):
    """Configure logging to work well with Google Cloud Run"""
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, assume it's configured
    if logger.handlers:
        return logger
        
    # Create a handler that logs to stderr (which Cloud Run captures)
    handler = logging.StreamHandler(sys.stderr)
    
    # Format logs in JSON format for better GCP integration
    log_format = '{"severity": "%(levelname)s", "message": "%(message)s", "timestamp": "%(asctime)s", "logger": "%(name)s"}'
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%dT%H:%M:%S%z')
    handler.setFormatter(formatter)
    
    # Set the log level from environment variable or default to INFO
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger

# Configure the module's logger
logger = setup_logging(__name__)


def pretty_json(obj: Any, indent: int = 2) -> str:
    """Pretty print JSON with proper formatting"""
    try:
        if isinstance(obj, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(obj)
                return json.dumps(parsed, ensure_ascii=False, indent=indent)
            except:
                return obj
        return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)
    except Exception:
        return str(obj)


async def inspect_session_state_and_artifacts(session_service, session_id, artifact_service, logger):
    """Inspect and pretty print session state and artifacts"""
    
    logger.info("=" * 60)
    logger.info("🔍 FINAL INSPECTION")
    logger.info("=" * 60)
    
    # Get final session state
    final_session = await session_service.get_session(
        app_name="sequential_workflow",
        user_id="sequential_user_1",
        session_id=session_id
    )
    
    if final_session and final_session.state:
        logger.info("📊 SESSION STATE:")
        for key, value in final_session.state.items():
            logger.info(f"  🔑 {key}: {pretty_json(value) if len(str(value)) < 200 else str(value)[:200] + '... [TRUNCATED]'}")
    else:
        logger.info("📊 SESSION STATE: Empty")
    
    # Get artifacts
    try:
        # InMemoryArtifactService doesn't have a direct list method, so we'll check if there are any
        logger.info("\n📁 ARTIFACTS:")
        if hasattr(artifact_service, 'artifacts') and artifact_service.artifacts:
            for artifact_id, artifact in artifact_service.artifacts.items():
                logger.info(f"  📄 {artifact_id}: {artifact}")
        else:
            logger.info("  📄 No artifacts found")
    except Exception as e:
        logger.info(f"  📄 Could not inspect artifacts: {e}")
    
    logger.info("=" * 60)