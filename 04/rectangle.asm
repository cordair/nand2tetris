// rectangle with width = 16, height = RAM[0]

@SCREEN
D=A
@addr
M=D

@R0
D=M
@n
M=D

@i
M=0

(FOR)
    @i
    D=M
    @n
    D=D-M
    @ENDFOR
    D;JE

    @addr
    A=M
    M=-1

    @i
    M=M+1
    @32
    D=A
    @addr
    M=D+M

    @FOR
    0;JMP
(ENDFOR)
@ENDFOR
0;JMP