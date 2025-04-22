import os
import time

import requests
import smtplib
import logging
from email.message import EmailMessage

env = os.environ
DATAFILE = "./data/ips.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s (%(name)s)] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def sendmail(iplist) -> bool:
    # send mail with new IPs
    message = EmailMessage()
    message['Subject'] = "New WAN IP-Address detected"
    message['From'] = env.get("MAILFROM")
    message['To'] = env.get("MAILTO")
    message.set_content(f"New IP(s) on interface {env.get("INTERFACE")}: \n{"\n".join(iplist)}")

    try:
        with smtplib.SMTP_SSL(env.get("MAILSERVER", ""), env.get("MAILSERVERPORT", "")) as server:
            server.login(env.get("MAILUSER"), env.get("MAILPASS"))
            server.send_message(message)
    except Exception as e:
        logging.error(f"Error while sending mail: {e}")
        return False
    else:
        return True


def check_ips():
    logging.info(f"Checking for IP changes...")
    # call the opnsense api to get the interface config
    try:
        response = requests.get(env.get("OPNSENSEURL") + "/api/diagnostics/interface/getinterfaceconfig",
                                auth=(env.get("OPNSENSEAPIKEY"), env.get("OPNSENSESECRET")),
                                timeout=5)
    except requests.exceptions.Timeout as e:
        logging.error(f"Timed out while checking IP changes: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error while checking IP changes: {e}")
        return False

    if response.status_code != 200:
        logging.error(f"Failed to connect to OPNsense API: {response.status_code} - {response.text}")
        return False

    interfaceconfig = response.json()

    # check if the interface is up
    if "up" not in interfaceconfig.get(env.get("INTERFACE")).get("flags"):
        logging.info("Interface is down")
        return False

    # extract ipv4 and ipv6 addresses from the interface
    ipinfos = (interfaceconfig.get(env.get("INTERFACE")).get("ipv4") +
               interfaceconfig.get(env.get("INTERFACE")).get("ipv6"))

    oldips = []
    ips = []

    for address in ipinfos:
        # if we have an ipaddress and it's not a link-local one, add to list
        if address.get("ipaddr") and not address.get("link-local"):
            ips.append(address.get("ipaddr"))

    if len(ips) == 0:
        # No IPs found - we stop here...
        logging.warning("No IPs found")
        return False

    # read old ips from file if it exists
    try:
        with open(DATAFILE, "r") as f:
            oldips = f.read().splitlines()
    except FileNotFoundError:
        pass

    # check if the ips have changed since last time
    if sorted(ips) != sorted(oldips):
        logging.info(f"IP(s) changed to {ips}. Sending mail to {env.get('MAILTO')}")
        if sendmail(ips) is True:
            # store new ips only when the mail was sent, otherwise we'll try again later
            logging.debug("Writing to file")
            with open(DATAFILE, "w") as f:
                f.write("\n".join(ips))
        else:
            return False
    else:
        logging.debug("Nothing changed")
    return True

if __name__ == "__main__":
    logging.info(f"Running...")
    try:
        while True:
            check_ips()
            time.sleep(int(env.get("INTERVAL", 60)))
    except KeyboardInterrupt:
        exit(0)
