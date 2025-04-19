# Tapo Exporter

A Prometheus and InfluxDB exporter for Tapo smart devices, built on top of the [mihai-dinculescu/tapo](https://github.com/mihai-dinculescu/tapo) library.

## Device Support

This exporter has been tested with the following Tapo devices:

- P110 Smart Plug
- P115 Smart Plug

> Note: While the underlying [mihai-dinculescu/tapo](https://github.com/mihai-dinculescu/tapo) library supports many more devices (L510, L520, L530, L535, L610, L630, L900, L920, L930, P100, P105, P300, P304, H100, S200B, KE100, T100, T110, T300, T310, T315), this exporter has only been tested with P110/P115 plugs. Support for other devices may be added in future versions.

## Credits

This project is built on top of the excellent [mihai-dinculescu/tapo](https://github.com/mihai-dinculescu/tapo) library, which provides the core functionality for interacting with Tapo devices. Special thanks to Mihai Dinculescu and all contributors for their work on the original library.

## Features

- Collects metrics from multiple Tapo P110/P115 smart plugs
- Exposes Prometheus metrics for:
  - Power consumption (watts)
  - Voltage (volts)
  - Current (amps)
  - Energy usage (watt-hours)
  - Runtime statistics
  - Device protection status
  - WiFi signal strength
- Configurable update interval
- Environment-based configuration using .env file

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/j4v3l/tapo-exporter.git
   cd tapo-exporter
   ```

2. Install the package:

   ```bash
   pip install -e .
   ```

## Configuration

Create a `.env` file in the project root with your device configurations:

```bash
# Number of devices to monitor
TAPO_DEVICE_COUNT=2

# Device 1 configuration (P110)
TAPO_DEVICE_1_NAME="Living Room"
TAPO_DEVICE_1_TYPE="p110"
TAPO_DEVICE_1_IP="192.168.1.100"
TAPO_DEVICE_1_EMAIL="your@email.com"
TAPO_DEVICE_1_PASSWORD="your_password"

# Device 2 configuration (P115)
TAPO_DEVICE_2_NAME="Kitchen"
TAPO_DEVICE_2_TYPE="p115"
TAPO_DEVICE_2_IP="192.168.1.101"
TAPO_DEVICE_2_EMAIL="your@email.com"
TAPO_DEVICE_2_PASSWORD="your_password"
```

Supported device types:

- `p110`: Tapo P110 Smart Plug
- `p115`: Tapo P115 Smart Plug (uses the same API interface as P110)

Note: Both P110 and P115 devices share the same API interface and capabilities. The device type is only used for identification purposes in the logs.

## Usage

Run the exporter:

```bash
tapo-exporter
```

The exporter will start collecting metrics from your configured Tapo devices and expose them on port 8000 by default.

## Metrics

The following metrics are collected:

- `tapo_device_count`: Total number of configured devices
- `tapo_power_watts`: Current power consumption
- `tapo_voltage_volts`: Current voltage
- `tapo_current_amps`: Current amperage
- `tapo_today_energy_wh`: Energy consumed today
- `tapo_month_energy_wh`: Energy consumed this month
- `tapo_power_saved_wh`: Power saved through energy-saving features
- `tapo_today_runtime_minutes`: Runtime today
- `tapo_month_runtime_minutes`: Runtime this month
- `tapo_power_protection_status`: Power protection status
- `tapo_overcurrent_status`: Overcurrent protection status
- `tapo_overheat_status`: Overheat protection status
- `tapo_signal_rssi`: WiFi signal strength

## Prometheus Configuration

Add the following to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'tapo'
    static_configs:
      - targets: ['localhost:8000']
```

## License

MIT License
