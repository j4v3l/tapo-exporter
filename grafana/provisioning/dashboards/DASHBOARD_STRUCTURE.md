# Tapo Dashboard Structure

## Overview

The Tapo Dashboard is designed to monitor and display metrics from Tapo smart plugs. It consists of several sections that provide both aggregated and per-device views of power consumption and related metrics.

## Dashboard Sections

### 1. Summary Panels (Top Row)

- **Power (Combined)**: Shows total power consumption across all devices
- **Watt-Hours (Combined)**: Shows total energy consumption across all devices
- **Current (Combined)**: Shows total current across all devices
- **Voltage (Mean)**: Shows average voltage across all devices
- **Device Count**: Shows number of active devices
- **Today's Cost**: Shows cost of energy consumption based on current rate

### 2. Device Metrics Log

A detailed log view showing all metrics for all devices, including:

- Power (watts)
- Energy (watt-hours)
- Current (amps)
- Voltage (volts)
- Month energy (watt-hours)
- Today runtime (minutes)
- Signal strength

### 3. Per-Device Panels

Each device has its own row of panels showing:

- Power (watts)
- Energy (watt-hours)
- Current (amps)
- Voltage (volts)

## Data Source

The dashboard uses InfluxDB as its data source, with the following configuration:

- Bucket: "tapo"
- Measurement: "tapo_metrics"
- Fields: Various metrics as described above

## Variables

- **Device**: A multi-select variable that allows filtering metrics by specific devices

## Refresh Rate

The dashboard automatically refreshes every 5 seconds to show real-time data.

## Time Range

By default, the dashboard shows data from the last 5 minutes to the current time.
