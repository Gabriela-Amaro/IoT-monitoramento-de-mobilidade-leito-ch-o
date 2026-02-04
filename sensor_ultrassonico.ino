#include <WiFi.h>
#include <PubSubClient.h>
#include <math.h>

// --- WIFI/MQTT ---
const char* ssid = "IFNMG-VISITANTES";
const char* password = "visitante";
const char* mqtt_server = "192.168.18.234";

// --- HC-SR04 ---
#define TRIG_PIN 5
#define ECHO_PIN 18

// --- BUZZER ---
#define BUZZER_PIN 4

// --- MQTT ---
WiFiClient espClient;
PubSubClient client(espClient);

void conectarWiFi() {
  Serial.print("Conectando-se ao WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void conectarMQTT() {
  while (!client.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (client.connect("ESP32_ULTRASONICO_BUZZ")) {
      Serial.println(" conectado!");
    } else {
      Serial.print(" falhou, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5s...");
      delay(5000);
    }
  }
}

// Retorna distância em cm (ou NAN se falhar)
float lerDistanciaCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duracao = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duracao == 0) return NAN;

  return (duracao * 0.0343f) / 2.0f;
}

// Bip curto (evita ficar apitando contínuo)
void beepCurto() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(5000);
  digitalWrite(BUZZER_PIN, LOW);
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  conectarWiFi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    conectarMQTT();
  }
  client.loop();

  float d = lerDistanciaCM();
  if (isnan(d)) {
    Serial.println("Falha ao ler o ultrassonico (timeout)!");
    digitalWrite(BUZZER_PIN, LOW);
    delay(1000);
    return;
  }

  // Alerta: entre 100cm e 150cm 
  bool alerta = (d >= 30.0 && d <= 100.0);

  // Serial
  Serial.print("Distancia: ");
  Serial.print(d, 1);
  Serial.print(" cm | Alerta: ");
  Serial.println(alerta ? "SIM" : "NAO");

  // Buzzer
  if (alerta) {
    beepCurto();
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }

  // MQTT
  char payload[120];
  snprintf(payload, sizeof(payload),
           "{\"distancia_cm\":%.1f,\"alerta\":%s}",
           d, alerta ? "true" : "false");

  client.publish("lab/03/ultrasonico", payload);

  delay(3000);
}