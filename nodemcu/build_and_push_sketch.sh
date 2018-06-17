set -e

export VERSION=$(python3 -c "import re;print(re.search('const char \* VERSION\s+=\s+\"(.*)\"', open('nodemcu.ino', 'rt').read()).group(1))")

export LOCAL_FIRMWARE_FILENAME=nodemcu_firmware_localcopy/nodemcu.bin.ver${VERSION}
if [ -f ${LOCAL_FIRMWARE_FILENAME} ]
then
    echo The file ${LOCAL_FIRMWARE_FILENAME} already exists! Did you forget to increment the VERSION in the arduino sketch?
    exit -1;
fi

rm -rf build
mkdir build
arduino-builder -build-path=$(pwd)/build -build-options-file="build.options.json" nodemcu.ino


scp build/nodemcu.ino.bin ${LOCAL_FIRMWARE_FILENAME}

scp build/nodemcu.ino.bin knutj@robots.knutj.org:/home/knutj/vannpumpelogserver/nodemcu_firmware/nodemcu.ini.bin.tmp
ssh knutj@robots.knutj.org mv /home/knutj/vannpumpelogserver/nodemcu_firmware/nodemcu.ini.bin.tmp /home/knutj/vannpumpelogserver/nodemcu_firmware/nodemcu.bin.ver${VERSION}

rm -rf build
echo Exported nodemcu firmware version ${VERSION}
