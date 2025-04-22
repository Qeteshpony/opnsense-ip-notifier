# OPNsense IP change notifications via email

This little script uses the opnsense api to check for changes on your
wan interface (by default) once a minute and notifies you if the IP(s) have changed

- create an api key on your opnsense
- clone this repository to your docker host
- copy notify.example.env to notify.env and fill in the variables
- run `docker compose up -d`
