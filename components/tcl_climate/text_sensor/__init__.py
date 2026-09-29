import esphome.codegen as cg
from esphome.components import text_sensor
import esphome.config_validation as cv

from ..climate import TclClimate

CONF_TCL_CLIMATE_ID = "tcl_climate_id"
CONF_FAN_SPEED = "fan_speed"
CONF_FAULT = "fault"
CONF_PROTOCOL_PROFILE = "protocol_profile"
CONF_FAN_SPEED_THRESHOLDS = "fan_speed_thresholds"
CONF_LOW = "low"
CONF_MEDIUM = "medium"
CONF_HIGH = "high"
CONF_TURBO = "turbo"

_THRESHOLD_KEYS = (CONF_LOW, CONF_MEDIUM, CONF_HIGH, CONF_TURBO)


def _validate_thresholds(value):
    values = [value[key] for key in _THRESHOLD_KEYS]
    if any(a >= b for a, b in zip(values, values[1:])):
        raise cv.Invalid("fan_speed_thresholds must increase: low < medium < high < turbo")
    return value


# Raw fan-speed boundaries for the fan_speed label. Nonzero speeds below `low`
# are reported as QUIET. Defaults reproduce the original labels.
FAN_SPEED_THRESHOLDS_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Optional(CONF_LOW, default=1): cv.int_range(min=1, max=255),
            cv.Optional(CONF_MEDIUM, default=86): cv.int_range(min=1, max=255),
            cv.Optional(CONF_HIGH, default=99): cv.int_range(min=1, max=255),
            cv.Optional(CONF_TURBO, default=118): cv.int_range(min=1, max=255),
        }
    ),
    _validate_thresholds,
)

TEXT_SENSORS = {
    CONF_FAN_SPEED: text_sensor.text_sensor_schema(
        icon="mdi:wind-power",
    ),
    CONF_FAULT: text_sensor.text_sensor_schema(
        icon="mdi:alert-circle-outline",
        entity_category="diagnostic",
    ),
    CONF_PROTOCOL_PROFILE: text_sensor.text_sensor_schema(
        icon="mdi:tune-variant",
        entity_category="diagnostic",
    ),
}

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(CONF_TCL_CLIMATE_ID): cv.use_id(TclClimate),
        }
    ).extend(
        {
            cv.Optional(key): schema
            for key, schema in TEXT_SENSORS.items()
        }
    ).extend({cv.Optional(CONF_FAN_SPEED_THRESHOLDS): FAN_SPEED_THRESHOLDS_SCHEMA}),
    cv.has_at_least_one_key(*TEXT_SENSORS),
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_TCL_CLIMATE_ID])

    for key in TEXT_SENSORS:
        if conf := config.get(key):
            entity = await text_sensor.new_text_sensor(conf)
            cg.add(getattr(parent, f"set_{key}_text_sensor")(entity))

    if thresholds := config.get(CONF_FAN_SPEED_THRESHOLDS):
        cg.add(
            parent.set_fan_speed_thresholds(
                *(thresholds[key] for key in _THRESHOLD_KEYS)
            )
        )
