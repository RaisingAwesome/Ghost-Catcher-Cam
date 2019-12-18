import os
ssid="hello"
pwd="goodbye"
os.system("echo \"ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\\nupdate_config=1\\ncountry=US\\n\\nnetwork={\\nssid=\\\"" + ssid + "\\\"\\npsk=\\\"" + pwd + "\\\"\\nkey_mgmt=WPA-PSK\\n}\\n\" > /home/pi/Ghost-Catcher-Cam/tempwifi.cfg")
os.system("more tempwifi.cfg")
exit()

