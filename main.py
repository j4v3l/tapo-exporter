import asyncio
import datetime
import os
import subprocess

from dotenv import load_dotenv
from tapo import ApiClient
from tapo.requests import EnergyDataInterval

# Load variables from .env file
load_dotenv()

IP = os.getenv("TAPO_IP")
EMAIL = os.getenv("TAPO_EMAIL")
PASSWORD = os.getenv("TAPO_PASSWORD")


def is_device_reachable(ip):
    try:
        if os.name == "nt":  # Windows
            ping_cmd = ["ping", "-n", "1", ip]
        else:  # macOS / Linux
            ping_cmd = ["ping", "-c", "1", ip]

        print(f"Pinging device with command: {' '.join(ping_cmd)}")  # Debug
        result = subprocess.run(
            ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Ping failed with exception: {e}")
        return False


def get_quarter_start_month(today: datetime.datetime) -> int:
    return 3 * ((today.month - 1) // 3) + 1


async def main():
    if not is_device_reachable(IP):
        print(f"Device at {IP} is not reachable. Make sure it's online.")
        exit(1)

    client = ApiClient(EMAIL, PASSWORD)
    device = await client.p110(IP)  # Use appropriate model for your plug

    await device.on()
    print("Plug turned ON.")

    # Device info
    info_json = await device.get_device_info_json()
    print("\nDevice Status:")
    print("==============")
    print(f"Power Protection Status: {info_json['power_protection_status']}")
    print(f"Overcurrent Status: {info_json['overcurrent_status']}")
    print(f"Overheat Status: {info_json['overheat_status']}")
    print(
        f"Signal Strength: Level {info_json['signal_level']} "
        f"(RSSI: {info_json['rssi']} dBm)"
    )
    print(f"Device Runtime: {info_json['on_time']} seconds")
    print(f"Device Model: {info_json['model']}")
    print(f"Firmware Version: {info_json['fw_ver']}")

    # Current power + calculated current
    try:
        current_power = await device.get_current_power()
        power_dict = current_power.to_dict()

        print("\nRaw Power Data (for debugging):")
        print("===============================")
        for k, v in power_dict.items():
            print(f"{k}: {v}")

        power_w = power_dict.get("current_power")
        voltage_v = power_dict.get("voltage")

        # Fallback if voltage is missing
        if voltage_v is None:
            voltage_v = 120.0  # or 230.0 depending on your region
            print(
                "⚠️ Voltage not reported by device. Using default 120V for calculation."
            )

        if power_w is not None and voltage_v:
            calculated_current = power_w / voltage_v
        else:
            calculated_current = None

        reported_current = power_dict.get("current")

        print(f"\nCurrent Power Consumption: {power_w} W")
        print(f"Voltage (used for calculation): {voltage_v} V")
        print(f"Reported Current: {reported_current} A")

        if calculated_current is not None:
            print(f"Estimated Current (Power / Voltage): {calculated_current:.4f} A")
        else:
            print("Could not calculate current due to missing data.")

    except Exception as e:
        print(f"\nCould not get current power: {e}")

    # Device usage
    try:
        device_usage = await device.get_device_usage()
        usage_dict = device_usage.to_dict()
        print("\nRuntime Statistics:")
        print("==================")
        print("Today's Usage:")
        print(f"  Runtime: {usage_dict['time_usage']['today']} minutes")
        print(f"  Energy: {usage_dict['power_usage']['today']} Wh")
        print(f"  Power Saved: {usage_dict['saved_power']['today']} Wh")

        print("\nPast 7 Days:")
        print(f"  Runtime: {usage_dict['time_usage']['past7']} minutes")
        print(f"  Energy: {usage_dict['power_usage']['past7']} Wh")
        print(f"  Power Saved: {usage_dict['saved_power']['past7']} Wh")

        print("\nPast 30 Days:")
        print(f"  Runtime: {usage_dict['time_usage']['past30']} minutes")
        print(f"  Energy: {usage_dict['power_usage']['past30']} Wh")
        print(f"  Power Saved: {usage_dict['saved_power']['past30']} Wh")
    except Exception as e:
        print(f"\nCould not get device usage: {e}")

    # Energy usage today/month
    try:
        energy_usage = await device.get_energy_usage()
        usage_dict = energy_usage.to_dict()
        print("\nDetailed Energy Usage:")
        print("=====================")
        print(f"Current Power: {usage_dict['current_power']} mW")
        print(f"Today's Runtime: {usage_dict['today_runtime']} minutes")
        print(f"Today's Energy: {usage_dict['today_energy']} Wh")
        print(f"Month's Runtime: {usage_dict['month_runtime']} minutes")
        print(f"Month's Energy: {usage_dict['month_energy']} Wh")
        print(f"Local Time: {usage_dict['local_time']}")
    except Exception as e:
        print(f"\nCould not get energy usage: {e}")

    # Hourly energy today
    try:
        today = datetime.datetime.today()
        energy_data_hourly = await device.get_energy_data(
            EnergyDataInterval.Hourly, today
        )
        hourly_data = energy_data_hourly.to_dict()
        print("\nHourly Energy Consumption Today:")
        print("===============================")
        for hour, power in enumerate(hourly_data["data"]):
            if power > 0:
                print(f"Hour {hour}: {power} Wh")
    except Exception as e:
        print(f"\nCould not get energy data: {e}")


if __name__ == "__main__":
    asyncio.run(main())
