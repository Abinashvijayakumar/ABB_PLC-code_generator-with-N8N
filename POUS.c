void MAIN_init__(MAIN *data__, BOOL retain) {
  __INIT_LOCATED(BOOL,__IX0_0,data__->STARTBUTTON,retain)
  __INIT_LOCATED_VALUE(data__->STARTBUTTON,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__QX0_0,data__->MOTOR,retain)
  __INIT_LOCATED_VALUE(data__->MOTOR,__BOOL_LITERAL(FALSE))
}

// Code part
void MAIN_body__(MAIN *data__) {
  // Initialise TEMP variables

  __SET_LOCATED(data__->,MOTOR,,__GET_LOCATED(data__->STARTBUTTON,));

  goto __end;

__end:
  return;
} // MAIN_body__() 





