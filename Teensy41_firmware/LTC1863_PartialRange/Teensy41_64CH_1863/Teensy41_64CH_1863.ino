// Feb. 2020:" This version of code uses new fiber optic board with different output channels connected to the four amplifier boards.  BoardMap variable has been updated.  

#include "hardware.h"
#include "util.h"
// #include "t3spi.h"
#include <SPI.h>
#include <Arduino.h>

//calibration data

bool should_next = false;
bool waiting_upload = false;


volatile int counter = 0;
volatile int cint = 0;

volatile long tHigh = 0;
volatile long tIrupt = 0;
volatile bool outHigh = false;
volatile int t;
String inputString = "";
bool stringComplete = false;


const int ctrlBuffer_length = 100;
char ctrlBuffer[ctrlBuffer_length];

// CHANGE WITH THE NUMBER OF CHANNELS USED
int8_t channels_used[NUM_B][NUM_C]  =
{
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
  {0, 1, 2, 3, 4, 5, 6, 7},
};

/******************************************************/
/*********************** IRUPT ************************/
/******************************************************/
long timey;
bool first = 0;
void setDACVal() {
  int repIdx;
  int blkIdx = computeBlockIdx(counter);
  if (blkIdx == -1) {
    blkIdx = 0; repIdx = 0;
    counter = 0;
  } else {
    repIdx = computeRepIdx(counter, blkIdx);
  }
  Serial.print("counter: ");
  Serial.println(counter);
  Serial.print("blkIdx: ");
  Serial.println(blkIdx);
  Serial.print("repIdx: ");
  Serial.println(repIdx);
  update_outputs(blkIdx, repIdx);
  counter++;
  // optional BNC output July 2019
     if(bncOut){
        long tnow = millis();
        if(tnow > tIrupt && !outHigh){
          tHigh = tnow;
          digitalWrite(bncPin,HIGH);
    ////      Serial.println("High");
          outHigh = true;
          tIrupt = tnow;

        }

       tnow = millis();
        if(tnow > tIrupt + .013  && outHigh){
          digitalWrite(bncPin,LOW);
    ////      Serial.println("High");
          outHigh = false;
          tIrupt = tnow;

        }


        
      }
      long timeytmp = millis();
    ////  Serial.println(timeytmp-timey);
      timey = timeytmp;
  // end bnc optional segment

  //  if (counter <= 0) {
  //    counter = 39;
  //  }
}

//}

typedef enum read_mode {MODE_ACCEPT, MODE_HEADER, MODE_BODY} read_mode;
read_mode mode;


/******************************************************/
/*********************** SETUP ************************/
/******************************************************/

void setup() {
  mode = MODE_ACCEPT;
  read_in_flight = false;
  Serial.begin(115200);
  inputString.reserve(50);

  //SETUP board and function select 
  initIO();
  selectNone();
  spiInit();

  //Initialize calibration data
  for (int b = 0; b < NUM_B; b++) {
    selectBoard(b);
    for (int c = 0; c < NUM_C; c++) {
      zeroPoint[b][c] = 0;
      gain[b][c] = -1.6;
      //      LTC2656Write(WRITE_AND_UPDATE,channelMap[c],32768);
    }
  }


  for (int j = 0; j < NUM_B * NUM_C; j++) {
    channel_order[j] = -1;
    board_order[j] = -1;      
  }
  int i = 0;
  for (int b = 0; b < NUM_B; b++) {
    for (int c = 0; c < NUM_C; c++) {
      if (channels_used[b][c] != -1) {
        channel_order[i] = channels_used[b][c];
        board_order[i] = b;
        i = i + 1;
      } else {
        break;
      }
    }
  }

  delay(500);
     attachInterrupt(interruptPin, setDACVal, FALLING);  // <===== Uncomment this line to enable TRIGGERING
       
  //    attachInterrupt(4, setDACVal, RISING);
  Serial.println("I'm up");
  //selectBoard(0);
  

  delay(100);
  // NVIC_ENABLE_IRQ(IRQ_SPI1);
  t = micros();
  Serial.println("about to write");
  //  zero_all();
  Serial.println("finished write");
  delay(500);
  // SPI_SLAVE->packetCT = 0;
  // SPI_SLAVE->dataPointer = 0;

  //  Serial.println(measure_gain(2,0),1);

  Serial.println("lets do it");
  //  selectBoard(4);
  //  zero_all();
  selectBoard(0);
  delay(100);
  Serial.println(NUM_B);
  Serial.println(NUM_C);
  selectNone();
  compute_transitions_base();
  
}

// 功能

void handleSerialCommand(String command) {
  command.trim();  // 去除空格和换行

  if (command.length() == 0) return;

  if (command == "D") {
    for (int i = 0; i < 8; i++) {
      Serial.print("B0");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(0, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B1");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(1, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B2");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(2, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B3");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(3, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B4");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(4, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B5");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(5, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B6");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(6, i);
      
    }
    for (int i = 0; i < 8; i++) {
      Serial.print("B7");
      Serial.print("ch");
      Serial.print(i);
      Serial.print(" ");
      calibrate_channel(7, i);
      
    }

    // give_all_channel_current();

  } else if (command == "Z") {
    zero_all();
    // give_all_channel_current();

  } else if (command == "T") {
    setDACVal();
    // give_all_channel_current();

  } else if (command == "I") {
    // print_all();
    give_all_channel_current();

  } else if (command == "M") {
    counter = 0;
    cint = 0;
    should_next = false;
    Serial.println(counter);
    update_outputs(0, 0);
    counter += 1;
    give_all_channel_current();

  } else if (command == "E") {
    setup();  // 重新初始化
    // give_all_channel_current();

  } else if (command.startsWith("Ichannel")) {
    int firstComma = command.indexOf(',');
    int secondComma = command.indexOf(',', firstComma + 1);

      if (firstComma > 0 && secondComma > firstComma) {
        int board = command.substring(firstComma + 1, secondComma).toInt();
        int channel = command.substring(secondComma + 1).toInt();
        give_one_channel_current(board,channel);
      }

  } else if (command == "Icurrentall") {
    give_all_channel_current();

  } else if (command.startsWith("Track")) {
    int TfirstComma = command.indexOf(',');
    int TsecondComma = command.indexOf(',', TfirstComma + 1);
    int TthirdComma = command.indexOf(',', TsecondComma + 1);

    if (TfirstComma > 0 && TsecondComma > TfirstComma && TthirdComma > TsecondComma) {
      int Tboard = command.substring(TfirstComma + 1, TsecondComma).toInt();
      int Tchannel = command.substring(TsecondComma + 1, TthirdComma).toInt();
      float Tcurrent = command.substring(TthirdComma + 1).toFloat();

      // 例如设定电流
      if (Tcurrent >= -4 && Tcurrent <= 4) {
        
        selectBoard(Tboard);
        LTC2656Write(WRITE_AND_UPDATE, channelMap[Tchannel], computeDacVal_I(Tcurrent, Tboard, Tchannel));
        give_one_channel_current(Tboard,Tchannel);

      } else {
        Serial.println("❌ 当前电流超出范围！");
      }
    }
  } else if (command.startsWith("uploadcoef")){
    Serial.println("Ready to receive coefStore...");
    waiting_upload = true;
    delay(20);  

  }

    
  else {
    Serial.print("Unknown command: ");
    Serial.println(command);
  }

}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}



/******************************************************/
/*********************** MAIN LOOP ********************/
/******************************************************/



void loop() {
  //  if(bncOut & outHigh){
  //    long tnow = millis();
  //    if(tnow > tHigh + 100){
  //       digitalWrite(bncPin,LOW);
  //       outHigh = false;
  //       Serial.println("low");
  //    }
  //  }
  if (should_next) {
    //    zero_all();
    //    calibrate_all();
    //    update_outputs(counter);
    should_next = false;
    print_all();
  }
  switch (mode) {
    case MODE_ACCEPT:
      char incomingByte;
      if (stringComplete){
         handleSerialCommand(inputString);
         inputString = "";
         stringComplete = false;
      }
      if (waiting_upload) {
        if (read_float_dump()) {
            waiting_upload = false;
            Serial.println("✅ coefStore updated.");
        }
      }



      
      break;
    case MODE_HEADER:
      if (Serial.available()) {
        int ctrlBuff_readlen =
          Serial.readBytesUntil(0, ctrlBuffer, ctrlBuffer_length);
        read_ctrl_string(ctrlBuffer);
        mode = MODE_BODY;
      }
      break;
    case MODE_BODY:
      if (read_float_dump()) {
        mode = MODE_ACCEPT;
      }
      break;
  }


}
