// This is the version of this sketch. This must be incremented to get OTA updates to work.
const char * VERSION = "23";
const int EXPECTED_TEMPERATURE_DEVICE_COUNT = 3;
const int PUMP_RUNNING_COUNT_ON_LIMIT = 5;

//#define LOGPOST_INTERVAL 3600000 // The number of milliseconds between each regular log-message.
const int LOGPOST_INTERVAL = 60000; // The number of milliseconds between each regular log-message.
const int CHECK_FOR_UPDATE_INTERVAL = 30000; // The number of milliseconds between each check for a new version.

const int waterLevelMeasurementCount = 100;
const int waterLevelMeasurementDelay = 100;


#define WIFI_STATUS_LED_PIN D5
#define PUMP_PIN D6
#define WATER_LEVEL_PIN A0
#define ONE_WIRE_BUS D2


#include <ESP8266httpUpdate.h>

#include <OneWire.h>
#include <EEPROM.h>

#include <DallasTemperature.h>


/**
 * BasicHTTPClient.ino
 *
 *  Created on: 24.05.2015
 *
 */

#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

#define USE_SERIAL Serial

ESP8266WiFiMulti wiFiMulti;


// Set up the temperature sensors.
OneWire oneWire(ONE_WIRE_BUS); 
DallasTemperature sensors(&oneWire);




struct AcccessPoints {
  char ssid1[50];
  char password1[50];
  char ssid2[50];
  char password2[50];
  char ssid3[50];
  char password3[50];
};



String authorizationToken;

void setup() {

    USE_SERIAL.begin(115200);

    USE_SERIAL.println();
    USE_SERIAL.println();
    USE_SERIAL.println();
    USE_SERIAL.println("Hup! Here we are, waking up!");
    USE_SERIAL.print("Sketch version:");
    USE_SERIAL.println(VERSION);
    USE_SERIAL.print("ESP8266 Chip id: ");
    USE_SERIAL.println(ESP.getChipId());

    AcccessPoints accessPoints;
    EEPROM.begin(sizeof(accessPoints));
    EEPROM.get(0, accessPoints);

    // To add or change an accesspoint , set the ssid and password on one of the accesspoints in
    // the "accessPoints" struct and call the EEPROM.put() function. Upload the schetch and check that 
    // the microcontroller manages to connect to the new accesspoint. Then, remove the password from the
    // source code and comment out the strcpy(), EEPROM.put() and EEPROM.commit() function-calls.
    //strcpy(accessPoints.ssid1, "Johan");
    //strcpy(accessPoints.password1, "");

    //strcpy(accessPoints.ssid2, "Telenor9600hiv");
    //strcpy(accessPoints.password2, "");
    
    //strcpy(accessPoints.ssid3, "kk");
    //strcpy(accessPoints.password3, "");
     
    //EEPROM.put(0, accessPoints);

    //EEPROM.commit();


    if (strlen(accessPoints.ssid1) > 0) {
        wiFiMulti.addAP(accessPoints.ssid1, accessPoints.password1);
    }
    if (strlen(accessPoints.ssid2) > 0) {
        wiFiMulti.addAP(accessPoints.ssid2, accessPoints.password2);
    }
    if (strlen(accessPoints.ssid3) > 0) {
        wiFiMulti.addAP(accessPoints.ssid3, accessPoints.password3);
    }

    pinMode(WIFI_STATUS_LED_PIN, OUTPUT);
    pinMode(PUMP_PIN, INPUT);
    pinMode(WATER_LEVEL_PIN, INPUT);

    authorizationToken = String(ESP.getChipId());

    sensors.begin();
    USE_SERIAL.print(" Temperature getDeviceCount: "); 
    USE_SERIAL.println(sensors.getDeviceCount());
}

unsigned long lastLogPostTime = 0;
bool hasLoggedOnceAfterStartup = false;

unsigned long lastCheckForUpdateTime = 0;
bool hasCheckedForUpdateAfterStartup = false;

bool pumpWasRunningLastLoop = false;



bool sendMessage(JsonObject& reading) {
    HTTPClient http;
    bool success;

    USE_SERIAL.print("[HTTP] begin...\n");

    http.begin("http://robots.knutj.org/vannpumpelogserver/log"); //HTTP
    http.addHeader("AUTHORIZATION", authorizationToken);
    http.addHeader("Content-Type", "application/json");

    char jsonmessageBuffer[1024];
    
    reading.printTo(jsonmessageBuffer, sizeof(jsonmessageBuffer));

    int httpCode = http.POST(jsonmessageBuffer);

    // httpCode will be negative on error
    if(httpCode > 0) {
        // HTTP header has been send and Server response header has been handled
        USE_SERIAL.printf("[HTTP] POST... code: %d\n", httpCode);

        // file found at server
        String payload = http.getString();
        USE_SERIAL.println(payload);
        success = true;
    } else {
        USE_SERIAL.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
        success = false;
    }

    http.end();
    return success;
}


char *addr2str(DeviceAddress deviceAddress)
{
    static char return_me[18];
    static char *hex = "0123456789ABCDEF";
    uint8_t i, j;

    for (i=0, j=0; i<8; i++) 
    {
         return_me[j++] = hex[deviceAddress[i] / 16];
         return_me[j++] = hex[deviceAddress[i] & 15];
    }
    return_me[j] = '\0';

    return (return_me);
}

void checkForUpdate() {
  USE_SERIAL.println("[checkForUpdate] starting...");
  t_httpUpdate_return ret = ESPhttpUpdate.update("robots.knutj.org", 80, "/vannpumpelogserver/nodemcu_update", VERSION);
  switch(ret) {
    case HTTP_UPDATE_FAILED:
        USE_SERIAL.println("[checkForUpdate] Update failed.");
        break;
    case HTTP_UPDATE_NO_UPDATES:
        USE_SERIAL.println("[checkForUpdate] Update no Update.");
        break;
    case HTTP_UPDATE_OK:
        USE_SERIAL.println("[checkForUpdate] Update ok."); // may not called we reboot the ESP
        break;
  }
}


void loop() {
    unsigned long currentTime = millis();
    if (currentTime < lastLogPostTime) {
        // millis() has wrapped around.
        lastLogPostTime = 0;
    }
    unsigned long elapsedTimeSinceLastLog = currentTime - lastLogPostTime;
    if (elapsedTimeSinceLastLog > (LOGPOST_INTERVAL + 3600000)) {
        // The logmessage posting is more than one hour overdue. We will reboot in case something has gotten stuck somehow.
        USE_SERIAL.println("The logmessage posting is more than one hour overdue. We will reboot in case something has gotten stuck somehow");
        delay(1000);
        ESP.restart();
    }

    if((wiFiMulti.run() != WL_CONNECTED)) {
        USE_SERIAL.println("No wifi connection.");
        digitalWrite(WIFI_STATUS_LED_PIN, 0);
        delay(1000);
        return;    
    }
    digitalWrite(WIFI_STATUS_LED_PIN, 1);


    unsigned long timeSinceLastCheckForUpdate = currentTime - lastCheckForUpdateTime;
    if (!hasCheckedForUpdateAfterStartup || (timeSinceLastCheckForUpdate > CHECK_FOR_UPDATE_INTERVAL)) {
        hasCheckedForUpdateAfterStartup = true;
        lastCheckForUpdateTime = currentTime;
        checkForUpdate();
    }
  
/*    int currentDeviceCount = sensors.getDeviceCount();
    if(currentDeviceCount != EXPECTED_TEMPERATURE_DEVICE_COUNT) {
        USE_SERIAL.print("currentDeviceCount(");
        USE_SERIAL.print(currentDeviceCount);
        USE_SERIAL.print(") != EXPECTED_TEMPERATURE_DEVICE_COUNT(");
        USE_SERIAL.print(EXPECTED_TEMPERATURE_DEVICE_COUNT);
        USE_SERIAL.println("), so I will restart now");
        delay(1000);
        ESP.restart();
    }
*/

    /* TODO: enable this once we have a good pump-sensor.
    // Do some filtering on the pump-running state by polling the pin multiple times.
    int pumpRunningCount = 0;
    //unsigned long pumpValueSum = 0;
    const int pumpValueLoops = 1000;
    for (int i=0; i<pumpValueLoops; i++) {
        if (digitalRead(PUMP_PIN) == 1) {
            pumpRunningCount++;
        }
        //int pumpValue = analogRead(PUMP_PIN);
        //pumpValueSum += pumpValue;
        //USE_SERIAL.print("pumpValue:");
        //USE_SERIAL.println(pumpValue);
        
        delay(1);
    }
     */

    /*int averagePumpValue = pumpValueSum / pumpValueLoops;
        USE_SERIAL.print("averagePumpValue:");
        USE_SERIAL.println(averagePumpValue);
    bool pumpIsRunning = pumpRunningCount >= PUMP_RUNNING_COUNT_ON_LIMIT;
*/
    bool pumpIsRunning = false;
    delay(1000);
    


    unsigned long timeUntilNextLog;
    if (elapsedTimeSinceLastLog >= LOGPOST_INTERVAL) {
      timeUntilNextLog = 0;
    } else {
      timeUntilNextLog = LOGPOST_INTERVAL - elapsedTimeSinceLastLog;
    }

    //USE_SERIAL.print("pumpRunningCount:");
    //USE_SERIAL.println(pumpRunningCount);

    //USE_SERIAL.print("pumpIsRunning:");
    //USE_SERIAL.println(pumpIsRunning);

    int waterLevelAcc = 0;
    for (int i=0; i<waterLevelMeasurementCount ; i++) {
      waterLevelAcc += analogRead(WATER_LEVEL_PIN);
      delay(waterLevelMeasurementDelay);
    }
    int waterLevel = waterLevelAcc / waterLevelMeasurementCount;
    
    USE_SERIAL.print("waterLevel:");
    USE_SERIAL.println(waterLevel);
    
/*
    USE_SERIAL.print("pumpWasRunningLastLoop:");
    USE_SERIAL.println(pumpWasRunningLastLoop);

    USE_SERIAL.print("elapsedTimeSinceLastLog:");
    USE_SERIAL.println(elapsedTimeSinceLastLog);

    USE_SERIAL.print("timeUntilNextLog:");
    USE_SERIAL.println(timeUntilNextLog);
*/
    if (hasLoggedOnceAfterStartup && (pumpWasRunningLastLoop == pumpIsRunning) && (timeUntilNextLog > 0)) {
        // Nothing to do yet
        return;
    }
    hasLoggedOnceAfterStartup = true;

    USE_SERIAL.println("Starting temperatur readings...");

    sensors.requestTemperatures();
    delay(1000); // Wait for the temperature sensors to become ready

    StaticJsonBuffer<1024> jsonBuffer;
    JsonObject& reading = jsonBuffer.createObject();

    for (int sensorReadAttemptNr=1; sensorReadAttemptNr <= 10; sensorReadAttemptNr++) {
        sensors.requestTemperatures();
        delay(1000); // Wait for the temperature sensors to become ready

        boolean failedToGetATemperature = false;
        for (uint8_t index=0; index < sensors.getDeviceCount(); index++) {
            DeviceAddress deviceAddress;
            sensors.getAddress(deviceAddress, index);
            float temperature = sensors.getTempCByIndex(index);
            if ((temperature > -127) && (temperature < 127)) {
                reading[addr2str(deviceAddress)] = temperature;
            } else {
                USE_SERIAL.print("A temperatur reading failed. temperature:");
                USE_SERIAL.print(temperature);
                USE_SERIAL.println(". I'll retry.");
                delay(10);
                failedToGetATemperature = true;
            }
        }
        if (!failedToGetATemperature) {
          USE_SERIAL.println("Got all the temperatur readings.");
          break;
        }
    }
    USE_SERIAL.println("Finished temperatur readings.");

    reading["water-level"] = waterLevel;

    if (pumpWasRunningLastLoop != pumpIsRunning) {
        // Send an extra message with the last pump-status. This makes it easier to plot the data with a simple line-diagram.
        reading["pump-running"] = pumpWasRunningLastLoop ? 1 : 0;
        if (!sendMessage(reading)) {
            return;
        }
    }
    //reading["pump-running"] = pumpIsRunning ? 1 : 0;
    if (!sendMessage(reading)) {
        return;
    }
    lastLogPostTime = millis();

    pumpWasRunningLastLoop = pumpIsRunning;
}

