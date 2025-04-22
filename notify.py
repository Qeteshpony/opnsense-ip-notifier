import os
import requests
import smtplib
from email.message import EmailMessage

env = os.environ
DATAFILE = "/data/ips.txt"

def sendmail(iplist):
    print("Sending mail...")
    message = EmailMessage()
    message['Subject'] = "New WAN IP-Address"
    message['From'] = env.get("MAILFROM")
    message['To'] = env.get("MAILTO")
    message.set_content(f"New WAN IP-Address: \n{"\n".join(iplist)}")

    with smtplib.SMTP_SSL(env.get("MAILSERVER", ""), env.get("MAILSERVERPORT", "")) as server:
        server.login(env.get("MAILUSER"), env.get("MAILPASS"))
        server.send_message(message)

response = requests.get(env.get("OPNSENSEURL") + "/api/diagnostics/interface/getinterfaceconfig",
                        auth=(env.get("OPNSENSEAPIKEY"), env.get("OPNSENSESECRET")))

interfaceconfig = response.json()

ipinfos = interfaceconfig.get(env.get("INTERFACE")).get("ipv4") + interfaceconfig.get(env.get("INTERFACE")).get("ipv6")

oldips = []
ips = []

for address in ipinfos:
    if address.get("ipaddr") and not address.get("link-local"):
        ips.append(address.get("ipaddr"))

try:
    with open(DATAFILE) as f:
        oldips = f.read().splitlines()
except FileNotFoundError:
    pass

if sorted(ips) != sorted(oldips):
    with open(DATAFILE, "w") as f:
        f.write("\n".join(ips))
    sendmail(ips)
else:
    print("Nothing changed")
