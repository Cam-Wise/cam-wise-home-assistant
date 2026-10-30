"""Constants for the Cam-Wise integration."""

DOMAIN = "cam_wise"
INTEGRATION_VERSION = "0.1.1b0"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_HOST = "host"
CONF_PORT = "port"
CONF_CAMERA_ENTITY = "camera_entity_id"
CONF_MOTION_ENTITY = "motion_entity_id"
CONF_DING_ENTITY = "ding_entity_id"
CONF_RECORDING_ENTITY = "recording_entity_id"

DEFAULT_PORT = 8000
SUPPORTED_API_VERSION = "1"
RECORDING_CONTRACT = 2
UPDATE_INTERVAL_SECONDS = 30

DISCOVERY_PATH = "/integrations/home-assistant/discovery-info"
STATUS_PATH = "/integrations/home-assistant/status"
HEALTH_PATH = "/health"
EVENT_PATH = "/integrations/home-assistant/cam-wise/event"
INTEGRATION_STATUS_PATH = "/integrations/home-assistant/cam-wise/status"
