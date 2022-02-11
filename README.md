# SARTopo in a box
## Setting up CalTopo/SARTopo Desktop on a Raspberry Pi

## Prerequisties
* Raspberry Pi 4 with 4+GB RAM
* Power supply
* MicroSD card
* CalTopo Desktop or Team subscription

## Download CalTopo Desktop
Download the "jar only" version of [CalTopo Desktop](https://caltopo.com/offline/app) and save it to your USB drive.

## Install Java 8
Initial testing with the default Java version was not acceptable, but those tests were run on the MicroSD, which may have been responsible for poor execution. There has been success running against Java 8 on a USB flash drive.
```
sudo apt-get update
sudo apt-get install openjdk-8-jre
sudo update-alternatives --config java
```

## Start CalTopo Desktop
```
java -Xmx2048m -jar desktop.jar
```
