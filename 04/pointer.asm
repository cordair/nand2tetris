// for (i = 0; i < n; i++) {
//    arr[i] = -1;    
// }

// arr = 100, n = 10
@100
D=A
@arr
M=D

@10
D=A
@n
M=D

@i
M=0

@FOR
@i
D=M
@n
D=D-M
@ENDFOR
D;JEQ

@i
D=M
@arr
A=D+M
M=-1

@i
M=M+1

@FOR
0;JMP

(ENDFOR)
@ENDFOR
0;JMP