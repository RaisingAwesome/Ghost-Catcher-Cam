if (ps -A | grep -w "python3") then 
	echo found
else
        sudo sh -c 'echo "0" > /sys/class/backlight/soc\:backlight/brightness'
	sudo shutdown now
fi
