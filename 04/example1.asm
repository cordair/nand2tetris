// Computes: if R0 > 0
//              R1 = 1
//           else 
//              R1 = 0

@IF
@R0
D=M

@ELSE
D;JGT
@R1
M=1

(ELSE)
@R1
M=0
(END)
@END
0;JMP