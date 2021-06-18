// RAM[1] = 1+2+...+n
// n in RAM[0]

// assigning variables
@R0
D=M
@n
M=D
@i
M=1
@sum
M=0

@FOR
// check if i > n
@i
D=M
@n
D=D-M
@ENDFOR
D;JGT

// update sum
@i
D=M
@sum
M=D+M

// update i
@i
M=M+1

@FOR
0;JMP

(ENDFOR)
@n
D=M
@R1
M=D

(END)
@END
0;JMP