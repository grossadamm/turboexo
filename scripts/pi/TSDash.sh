#!/bin/sh
ARCH=$( uname -m )
KERNEL=$( uname -s )
SCRIPT=$0

while [ -h "$SCRIPT" ]; do
	SCRIPT=$( readlink "$SCRIPT" )
done

BASE_PATH="${SCRIPT%/*}"
LAST_PATH="$PWD"

if [ ! -e "$BASE_PATH/TSDash.properties" ]; then
	echo "This script must be located in the TunerDash directory. To be able"
	echo "to launch without path create a symlink of this script to a directory in PATH."
	echo
	echo "Example: ln -s /home/john_doe/EcuDashHub/EcuEashHub.sh /usr/local/bin"
	exit 1
fi

# Java's native splash appears before the JVM initializes and closes when
# TSDash maps its first AWT/Swing window. It prevents TSDash's white startup
# frame even if the animated overlay fails or maps late.
cd "$BASE_PATH" || exit 1
if [ "$#" -gt 0 ]; then
	java -splash:boot/exocet-boot-v2.png -jar TSDash.jar "$1"
else
	java -splash:boot/exocet-boot-v2.png -jar TSDash.jar
fi
RESULT=$?

if [ -d "$LAST_PATH" ]; then
	cd "$LAST_PATH" || true
fi

exit $RESULT
