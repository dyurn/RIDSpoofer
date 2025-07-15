import argparse
import logging
import random
from datetime import datetime, timedelta

from scapy.config import conf

from spoof_drones import (
    ParseLocationAction,
    create_packet,
    get_random_serial_number,
    get_random_pilot_location,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Drone Autopilot Spoofer",
        description="Spoof one drone and move it automatically in a human like pattern",
    )
    parser.add_argument("-i", "--interface", help="interface name")
    parser.add_argument(
        "-l",
        "--location",
        nargs=2,
        metavar=("LATITUDE", "LONGITUDE"),
        action=ParseLocationAction,
        required=True,
        help="start location of the drone",
    )
    parser.add_argument(
        "-n",
        "--interval",
        type=float,
        default=1,
        help="interval in seconds between packets",
    )
    parser.add_argument(
        "-s",
        "--serial",
        type=lambda x: x if 20 >= len(x) > 0 else False,
        help="set drones serial number",
    )
    return parser.parse_args()


def human_like_step(lat: int, lng: int, direction: int, step: int = 1000) -> tuple[int, int, int]:
    """Generate the next coordinate with small random jitter"""
    lat += random.randint(-step, step)
    lng += random.randint(-step, step)
    direction = (direction + random.randint(-30, 30)) % 360
    return lat, lng, direction


def spoof_autopilot_drone(args: argparse.Namespace) -> None:
    seconds: float = args.interval
    lat, lng = args.location
    serial = args.serial.encode() if args.serial else get_random_serial_number()
    pilot_loc = get_random_pilot_location(lat, lng)
    direction = 0

    logging.info(
        f"Creating autopilot drone SERIAL={serial} starting at lat={lat}, lng={lng}"
    )

    send_next = datetime.now()
    s = conf.L2socket(iface=args.interface or "wlan1")
    try:
        while True:
            if send_next <= datetime.now():
                lat, lng, direction = human_like_step(lat, lng, direction)
                packet = create_packet(lat, lng, serial, pilot_loc, direction)
                s.send(packet)
                logging.info(
                    f"Sent {serial} at lat={lat} lng={lng} direction={direction}"
                )
                send_next = datetime.now() + timedelta(seconds=seconds)
    except KeyboardInterrupt:
        logging.info("Script interrupted. Shutting down..")
    finally:
        s.close()


def main() -> None:
    args = parse_args()
    spoof_autopilot_drone(args)


if __name__ == "__main__":
    main()
