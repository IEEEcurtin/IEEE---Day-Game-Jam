const int PIEZO = 34; 

void setup() { 
  Serial.begin(115200); 
} 

void loop() { 
	int value = analogRead(PIEZO); 
	
	Serial.println(value); 
	delay(50); 
}
