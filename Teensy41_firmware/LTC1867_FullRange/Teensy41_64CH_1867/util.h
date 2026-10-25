
/******************************************************/
/*************** STATE FOR DATA TRANSFER **************/
/******************************************************/

// 
const int maxBlocks = 10;
int channels = 64; // number of  total channel, need to change with the board number
int blocks = 2; // 

// dummy test case 
// HERE, ZHIHUA change the number from 6 to 100
int lengths[maxBlocks] = {100,2}; 
int reps[maxBlocks] = {10000,3};


int block_transitions[maxBlocks];
int block_base[maxBlocks];
bool lendian;

float coefStore[50000] = {    
 



//first block
// central transversal slice optimal current distribution
// ALL ZERO
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,







// 0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,
// 0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,
// 0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,
// 0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,
// 0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,





};


float coefStoreAsMat(int chanIdx, int blockIdx, int repIdx);
/******************************************************/
/*********************** UTILITY CALCULATIONS *********/
/******************************************************/


uint16_t computeDacVal_V(float voltage, int b, int c) {
  return uint16_t((65535.0 * (voltage - zeroPoint[b][c]) / 5.0));
}

uint16_t computeDacVal_I(float current, int b, int c) {
  return uint16_t((65535.0 * (current / gain[b][c] + 2.5 - zeroPoint[b][c]) / 5.0));
}



float computeOutV(uint16_t dacVal) {
  return ((float(dacVal) * 4.096 / 65535.0));
}

float computeOutI(uint16_t dacVal) {
  return ((float(dacVal) * 4.096 / 65535.0) - 1.25) / 1.8 / 0.2;
}


/******************************************************/
/*********************** UTILITY *********************/
/******************************************************/
void zero_all() {  /// JPS changed from float
  for (int b = 0; b < NUM_B; b++) {
    selectBoard(b);
    for (int c = 0; c < NUM_C; c++) {
      LTC2656Write(WRITE_AND_UPDATE, channelMap[c], computeDacVal_I(0, b, c));
    }
  }
}

float measure_gain(uint8_t b, uint8_t c) {
  //jump to 2.0 first so output returns nutral;

  selectBoard(b);
  delay(1);
  LTC2656Write(WRITE_AND_UPDATE, channelMap[c], computeDacVal_V(2.0, b, c));//由(2.0, 0, 0)改为(2.0, b, c)
  delayMicroseconds(1000);
  uint16_t out_2v0 = LTC1863ReadSlow(c, 50);
  
  //Serial.print("Ch");
  //Serial.print(c );
  //Serial.print("\n");
  //Serial.print(out_2v0);
  //Serial.print("\n");
  //Serial.println(computeOutI(out_2v0),5);
  LTC2656Write(WRITE_AND_UPDATE, channelMap[c], computeDacVal_V(2.5, b, c));//由(2.5, 0, 0)改为(2.0, b, c)
  delayMicroseconds(1000);
  uint16_t out_2v5 = LTC1863ReadSlow(c, 50);
  //Serial.print("Ch");
  //Serial.print(c);
  //Serial.print("\n");
  //Serial.print(out_2v5);
  //Serial.print("\n");
  //Serial.println(computeOutI(out_2v5),5);

  return (computeOutI(out_2v5) - computeOutI(out_2v0)) / (0.5);
}

bool calibrate_channel(uint8_t b, uint8_t c) {
  zeroPoint[b][c] = 0;
  //gain[b][c]=0;
  delay(10);
  gain[b][c] = measure_gain(b, c);
  //Serial.print(gain[b][c]);
  if (abs(gain[b][c] + 1.62) > 0.5) { 
    //    gain[b][c] = 1.6;d
    Serial.println("failed (gain)");
    calibrationStatus[b][c] = false;
    return false;
  } else {
    //    return true;
  }

  //  Serial.print("gain: ");
  //  Serial.println(gain[b][c]);
  for (int i = 0; i < 20; i++) {
    float output_offset_I = computeOutI(LTC1863ReadSlow(c));
    //float testa;
    //    Serial.print("iteration: ");
    //    Serial.println(i);
    //Serial.println(output_offset_I,5);
    if (abs(output_offset_I) <= 0.001) {
      calibrationStatus[b][c] = true;
      Serial.print("Ch");
      Serial.print(c );
      Serial.print(" has been calibrated! \n");
      return true;
    }
    else{
      zeroPoint[b][c] = zeroPoint[b][c] + (output_offset_I / gain[b][c]);
    //    Serial.print("next: ");
    //    Serial.println(zeroPoint[b][c],5);
      LTC2656Write(WRITE_AND_UPDATE, channelMap[c], computeDacVal_I(0, b, c));
    }
    
    delay(25);   // changed from 10us to allow for slower amplifier rise times -- JPS 02/2020
  }
  Serial.println("failed (cal)");
  calibrationStatus[b][c] = false;
  zeroPoint[b][c] = 0;
  LTC2656Write(WRITE_AND_UPDATE, channelMap[c], computeDacVal_I(0, b, c));
  delay(10000);
  return false;
}

void calibrate_all() { // JPS changed from bool
  for (int b = 0; b < NUM_B; b++) {
    for (int c = 0; c < NUM_C; c++) {
      calibrate_channel(b, c);
    }
    delay(500);
  }
}

void print_all_boards() {
  for (int b = 0; b < NUM_B; b++) {
    selectBoard(b);
    Serial.println("---------------");
    Serial.print("B: ");
    Serial.println(b);
    for (int c = 0; c < NUM_C; c++) {
      Serial.print(c);
      Serial.print(": ");
      uint16_t data = LTC1863ReadSlow(c, 50);
      Serial.print(data, 4);
      Serial.print("\t");

      Serial.print(computeOutI(data), 4);
      Serial.print("\t");
       Serial.print(computeOutV(data), 4);
      Serial.print("\t");
      Serial.print(gain[b][c]);
      if (!calibrationStatus[b][c]) {
        Serial.println(" X");
      } else {
        Serial.println("");
      }

    }
  }
}

void update_outputs(int blkIdx, int repIdx) {
  int8_t b = 0;
  selectBoard(b);
  //Serial.println('-------------------------');  //JPS hacked june 2019
  Serial.println("-------------------------");
  for (int i = 0; i < NUM_C * NUM_B; i++) {
    int c = channel_order[i];
    if (c == -1 || c == -1) {
      break;
    }
    if (b != board_order[i]) {
      b = board_order[i];
      selectBoard(b);
    }

//    Serial.println(coefStoreAsMat(i, blkIdx, repIdx));
    LTC2656Write(WRITE_AND_UPDATE, channelMap[c],
                 computeDacVal_I(coefStoreAsMat(i, blkIdx, repIdx), b, c));

  }
}

void print_all() {
  int8_t b = 0;
  selectBoard(b);
  Serial.println("-------------");
  for (int i = 0; i < NUM_C * NUM_B; i++) {

    int c = channel_order[i];
    if (c == -1) {
      break;
    }
    if (b != board_order[i]) {
      b = board_order[i];
      selectBoard(b);
    }
    uint16_t data = LTC1863ReadSlow(c);
    // Serial.print(i);
    Serial.print("(");
    Serial.print(b);
    Serial.print(",");
    Serial.print(c);
    Serial.print(")\t");
    Serial.print(data, 4);
    Serial.print("\t");
    Ichannel[b][c] = computeOutI(data);
    Serial.print(Ichannel[b][c], 4);
    Serial.print("\t");
    // Serial.print(computeOutV(data), 4);
    // Serial.print("\t");
    Serial.print(gain[b][c]);
    if (!calibrationStatus[b][c]) {
      Serial.println(" X");
    } else {
      Serial.println("");
    }
  }
}


/******************************************************/
/************** READ CTRL STRING  *********************/
/******************************************************/

void read_ctrl_string(char * ctrlBuffer) {
  char* c = strchr(ctrlBuffer, 'c');
  char* bar = strchr(c, '|');
  bar[0] = 0;
  channels = atoi(c + 1);

  char* b = strchr(bar + 1, 'b');
  bar = strchr(b, '|');
  bar[0] = 0;
  blocks = atoi(b + 1);
  Serial.print("blocks:");
  Serial.println(blocks);

  char* l = strchr(bar + 1, 'l');
  char* nextl;
  Serial.println("lengths:");
  for (int i = 0; i < blocks; i++) {
    nextl = strchr(l + 1, '|');
    nextl[0] = 0;
    lengths[i] = atoi(l + 1);
    Serial.println(lengths[i]);
    l = nextl;
  }

  char* r = strchr(nextl + 1, 'r');
  char* nextr;
  Serial.println("repeats:");
  for (int i = 0; i < blocks; i++) {
    nextr = strchr(r + 1, '|');
    nextr[0] = 0;
    reps[i] = atoi(r + 1);
    Serial.println(reps[i]);
    r = nextr;
  }
  Serial.println("transitions:");
  block_transitions[0] = reps[0] * lengths[0];
  Serial.println(block_transitions[0]);
  for (int i = 1; i < blocks; i++) {
    block_transitions[i] = block_transitions[i - 1] + reps[i] * lengths[i];
    Serial.println(block_transitions[i]);
  }
  Serial.println("base:");
  block_base[0] = lengths[0];
  Serial.println(block_base[0]);
  for (int i = 1; i < blocks; i++) {
    block_base[i] = block_base[i - 1] + lengths[i];
    Serial.println(block_base[i]);
  }
}

void compute_transitions_base() {
  Serial.println("transitions:");
  block_transitions[0] = reps[0] * lengths[0];
  Serial.println(block_transitions[0]);
  for (int i = 1; i < blocks; i++) {
    block_transitions[i] = block_transitions[i - 1] + reps[i] * lengths[i];
    Serial.println(block_transitions[i]);
  }
  Serial.println("base:");
  block_base[0] = lengths[0];
  Serial.println(block_base[0]);
  for (int i = 1; i < blocks; i++) {
    block_base[i] = block_base[i - 1] + lengths[i];
    Serial.println(block_base[i]);
  }
}

/* BLOCKING !!!!
   TIMEOUT DETERMIEND BY SERIAL TIMEOUT*/
bool read_float_dump() {
  int totalLength = 0;
  for (int i = 0; i < blocks; i++) {
    totalLength += channels * lengths[i];
  }
  if (Serial.available()) {
    Serial.println("starting");
    Serial.readBytes((char*)coefStore, 4 * totalLength);
    Serial.println("done");
    return 1;
  }
  return 0;
}

int computeBlockIdx(int iter) {
  int blkIdx = 0;
  for (int i = 0; i < blocks; i++) {
    if (iter >= block_transitions[i]) {
      blkIdx = (i + 1);
    }
  }
  if (blkIdx >= blocks) {
    blkIdx = -1;
  }
  return blkIdx;
}

int computeRepIdx(int iter, int blkIdx) {
  int base = 0;
  if (blkIdx >= 1) {
    base = block_transitions[blkIdx - 1];
  }
  return (iter - base) % lengths[blkIdx];
}

float coefStoreAsMat(int chanIdx, int blkIdx, int repIdx) {
  int base = 0;
  if (blkIdx >= 1) {
    base = block_base[blkIdx - 1];
  }
  int idx = channels * (base + repIdx) + chanIdx;
  Serial.println(coefStore[idx]);

  return (coefStore[idx]);
}

void give_one_channel_current(int board, int channel) {
  selectBoard(board);
  Serial.print("Icurrent ");
  Serial.print(board);
  Serial.print(" ");
  Serial.print(channel);
  Serial.print(" ");
  uint16_t ADC_I = LTC1863ReadSlow(channel);
  Ichannel[board][channel] = computeOutI(ADC_I);
  Serial.print(Ichannel[board][channel], 4);
  Serial.print(" ");
  Serial.print(gain[board][channel]);
  if (!calibrationStatus[board][channel]) {
      Serial.println(" F");
  } else {
      Serial.println(" T");
  }
  
}

void give_all_channel_current() {
  Serial.print("Icurrentall\n");
  // Serial.print("\n");
  int8_t b = 0;
  selectBoard(b);
  for (int i = 0; i < NUM_C * NUM_B; i++) {

    int c = channel_order[i];
    if (c == -1) {
      break;
    }
    if (b != board_order[i]) {
      b = board_order[i];
      selectBoard(b);
    }
    uint16_t data = LTC1863ReadSlow(c);
    Serial.print(b);
    Serial.print(" ");
    Serial.print(c);
    Serial.print(" ");
    Ichannel[b][c] = computeOutI(data);
    Serial.print(Ichannel[b][c], 4);
    Serial.print(" ");
    Serial.print(gain[b][c]);
    if (!calibrationStatus[b][c]) {
      Serial.println(" F");
    } else {
      Serial.println(" T");
    }
  }
  Serial.print("IcurrentallEnd\n");
}

