// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

@SCREEN
D=A
@addr
M=D
@8192 // 32 * 256
D=A
@n
M=D

    (LOOP)
    @i
    M=0
    @addr
    D=M
    @p
    M=D

    @KBD
    D=M
    @CLEAR
    D;JEQ
    @DRAW
    0;JMP

        (DRAW)
        @i
        D=M
        @n
        D=D-M
        @ENDDRAW
        D;JEQ

        @p
        A=M
        M=-1
        @p
        M=M+1

        @i
        M=M+1
        @DRAW
        0;JMP

        (CLEAR)
        @i
        D=M
        @n
        D=D-M
        @ENDDRAW
        D;JEQ

        @p
        A=M
        M=0
        @p
        M=M+1

        @i
        M=M+1
        @CLEAR
        0;JMP
    (ENDDRAW)
    @LOOP
    0;JMP

