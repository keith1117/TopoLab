/* Original minimal Linux x86-64 entry, no C runtime startup. */
.text
.globl _start
.type _start,@function
_start:
    xor %ebp,%ebp
    mov %rsp,%rdi
    and $-16,%rsp
    sub $16,%rsp
    movl $0x1f80,(%rsp)
    ldmxcsr (%rsp)
    fninit
    add $16,%rsp
    call i1_main
    mov %eax,%edi
    mov $60,%eax
    syscall
    ud2
.size _start,.-_start
.section .note.GNU-stack,"",@progbits
