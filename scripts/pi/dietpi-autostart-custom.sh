#!/bin/bash
# Black X root from its first frame; .xinitrc owns the rest of the handoff.
# DietPi prints one autostart status line immediately before executing this
# script; erase it before Xorg starts drawing.
printf '\033[2J\033[H\033[?25l'
startx -- -nocursor -br

exit 0
