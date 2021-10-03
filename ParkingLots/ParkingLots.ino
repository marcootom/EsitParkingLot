#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <MQTT.h>
#include <ArduinoJson.h>
#include <time.h>

#define emptyString String()
// Error handling functions
#include "errors.h"
// Configuration data
#include "configuration.h"
#define NUM_STALLI 2

// Define MQTT port
const int MQTT_PORT = 8883;
// Define subscription and publication topics (on thing shadow)
const char MQTT_SUB_TOPIC[] = "$aws/things/" THINGNAME "/shadow/update";
const char MQTT_PUB_TOPIC[] = "$aws/things/" THINGNAME "/shadow/update";
// Enable or disable summer­time
#ifdef USE_SUMMER_TIME_DST
uint8_t DST = 1;
#else
uint8_t DST = 0;
#endif

// Create Transport Layer Security (TLS) connection
WiFiClientSecure net;
// Load certificates
BearSSL::X509List cert(cacert);
BearSSL::X509List client_crt(client_cert);
BearSSL::PrivateKey key(privkey);
// Initialize MQTT client
MQTTClient client;
unsigned long lastMs = 0;
time_t now;
time_t nowish = 1510592825;
/* VARIABILI PIN */
const int trigPin1 = D1;
const int echoPin1 = D2;
const int trigPin2 = D7;
const int echoPin2 = D8;
/**/
long duration;
int distance;

bool stalli[NUM_STALLI];

void NTPConnect(void)
{
  Serial.print("Setting time using SNTP");
  configTime(TIME_ZONE * 3600, DST * 3600, "pool.ntp.org", "time.nist.gov");
  now = time(nullptr);
  while (now < nowish)
  {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("done!");
  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  Serial.print("Current time: ");
  Serial.print(asctime(&timeinfo));
}

// MQTT management of incoming messages
void messageReceived(String &topic, String &payload)
{
  Serial.println("Received [" + topic + "]: " + payload);
  DynamicJsonDocument doc(2048);
  deserializeJson(doc, payload);

}

// MQTT Broker connection
void connectToMqtt(bool nonBlocking = false)
{
  Serial.print("MQTT connecting ");
  while (!client.connected())
  {
    if (client.connect(THINGNAME))
    { Serial.println("connected!");
      if (!client.subscribe(MQTT_SUB_TOPIC))
        lwMQTTErr(client.lastError());
    }
    else
    { Serial.print("SSL Error Code: ");
      Serial.println(net.getLastSSLError());
      Serial.print("failed, reason ­> ");
      lwMQTTErrConnection(client.returnCode());
      if (!nonBlocking) {
        Serial.println(" < try again in 5 seconds");
        delay(5000);
      }
      else {
        Serial.println(" <");
      }
    }
    if (nonBlocking) break;
  }
}

// Wi­Fi connection
void connectToWiFi(String init_str)
{
  if (init_str != emptyString)
    Serial.print(init_str);
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(1000);
  }
  if (init_str != emptyString)
    Serial.println("ok!");
}

void verifyWiFiAndMQTT(void)
{
  connectToWiFi("Checking WiFi");
  connectToMqtt();
}

unsigned long previousMillis = 0;
const long interval = 5000;

// MQTT management of outgoing messages
void sendData()
{
  DynamicJsonDocument jsonBuffer(255);
  JsonObject root = jsonBuffer.to<JsonObject>();
  JsonObject state = root.createNestedObject("state");
  JsonObject state_reported = state.createNestedObject("reported");
  state_reported["p"] = THINGNAME;
  
  JsonArray stalli_reported = state_reported.createNestedArray("s");
  
  for (int i = 0; i < NUM_STALLI; i++) {
    JsonObject state_stal = stalli_reported.createNestedObject();
    state_stal["id"] = i;
    state_stal["v"] = (int) stalli[i];
  }

  Serial.printf("Sending  [%s]: ", MQTT_PUB_TOPIC);
  serializeJson(root, Serial);
  Serial.println();
  char shadow[measureJson(root) + 1];
  serializeJson(root, shadow, sizeof(shadow));
  if (!client.publish(MQTT_PUB_TOPIC, shadow, false, 0))
    lwMQTTErr(client.lastError());
}

void setup()
{
  Serial.begin(115200);
  delay(5000);
  Serial.println();
  Serial.println();
  WiFi.hostname(THINGNAME);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);
  connectToWiFi(String("Trying to connect with SSID: ") + String(ssid));
  NTPConnect();
  net.setTrustAnchors(&cert);
  net.setClientRSACert(&client_crt, &key);
  client.begin(MQTT_HOST, MQTT_PORT, net);
  client.onMessage(messageReceived);
  connectToMqtt();
  /* SETUP PIN */
  pinMode(trigPin1, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin1, INPUT); // Sets the echoPin as an Input
  digitalWrite(trigPin1, HIGH);
  pinMode(trigPin2, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin2, INPUT); // Sets the echoPin as an Input
  digitalWrite(trigPin2, HIGH);
  /**/
}

void loop()
{
  now = time(nullptr);
  if (!client.connected())
  {
    verifyWiFiAndMQTT();
  }
  else
  {
    client.loop();
    for (int i = 0; i < NUM_STALLI; i++) {
      /* AZIONE SENSORE */
      if (i == 0) {       
        digitalWrite(trigPin1, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin1, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin1, LOW);
        duration = pulseIn(echoPin1, HIGH);
      }
      if (i == 1) {
        digitalWrite(trigPin2, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin2, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin2, LOW);
        duration = pulseIn(echoPin2, HIGH);
      }
      /**/
      Serial.printf("id: %d duration: %d\n", i, duration);
      if (stalli[i] && (duration * 0.034 / 2) <= 20)
      {
        if (millis() - lastMs >= 3000) {
          stalli[i] = false;
          sendData();
          lastMs = millis();
        }
      }
      else if (!stalli[i] && (duration * 0.034 / 2) > 20)
      {
        if (millis() - lastMs >= 3000) {
          stalli[i] = true;
          sendData();
          lastMs = millis();
        }
      }
      delay(250);
    }
  }
}
