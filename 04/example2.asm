//Swap values in Ram[0] and Ram[1]

@R0
D=M
@a
M=D

@R1
D=M
@R0
M=D

@a
D=M
@R1
M=D

(END)
@END
0;JMP