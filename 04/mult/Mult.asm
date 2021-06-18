// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// assign a,b,sum,i

@sum
M=0
@i
M=0

// sum=a+a+..+a (a appears b times)
    (FOR)
    @i
    D=M
    @R1
    D=D-M
    @ENDFOR
    D;JEQ

    @R0
    D=M
    @sum
    M=D+M

    @i
    M=M+1
    @FOR
    0;JMP
    (ENDFOR)

// assign result to R2
@sum
D=M
@R2
M=D

(RETURN)
@RETURN
0;JMP