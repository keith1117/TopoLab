/* All OS interactions are explicit Linux x86-64 syscalls. No libc, libm or loader. */
#include "runtime.h"

_Static_assert(sizeof(long)==8&&sizeof(int)==4&&sizeof(double)==8,"x86-64 ABI required");
long rt_call(long n,long a,long b,long c,long d,long e,long f) {
    register long r10 __asm__("r10")=d;
    register long r8 __asm__("r8")=e;
    register long r9 __asm__("r9")=f;
    long result;
    __asm__ volatile("syscall":"=a"(result):"a"(n),"D"(a),"S"(b),"d"(c),
                     "r"(r10),"r"(r8),"r"(r9):"rcx","r11","cc","memory");
    return result;
}
void *memcpy(void *target,const void *source,unsigned long n) {
    unsigned char *d=target; const unsigned char *s=source;
    for(unsigned long i=0;i<n;++i) d[i]=s[i];
    return target;
}
void *memset(void *target,int value,unsigned long n) {
    unsigned char *d=target;
    for(unsigned long i=0;i<n;++i) d[i]=(unsigned char)value;
    return target;
}
int rt_equal(const char *a,const char *b) {
    for(int i=0;i<256;++i) {if(a[i]!=b[i]) return 0;if(!a[i]) return 1;}
    return 0;
}
int rt_write(int fd,const void *source,unsigned long n) {
    unsigned long offset=0;
    for(int calls=0;calls<16384&&offset<n;++calls) {
        long size=rt_call(1,fd,(long)((const char *)source+offset),n-offset,0,0,0);
        if(size<=0) return 1;
        offset+=(unsigned long)size;
    }
    return offset!=n;
}
void rt_text(const char *s) {
    unsigned long n=0;while(n<16384&&s[n]) ++n;
    if(rt_write(1,s,n)) rt_call(60,74,0,0,0,0,0);
}
void rt_uint(unsigned long n) {
    char reversed[32],out[32];int count=0;
    do {reversed[count++]=(char)('0'+n%10);n/=10;} while(n&&count<32);
    for(int i=0;i<count;++i) out[i]=reversed[count-i-1];
    if(rt_write(1,out,count)) rt_call(60,74,0,0,0,0,0);
}
long rt_open_read(const char *name) {
    long fd=rt_call(257,-100,(long)name,0404000,0,0,0); /* NOFOLLOW|NONBLOCK */
    if(fd<0) return -1;
    /* Linux x86-64 UAPI stat ABI, no libc wrapper. Nonregular streams are refused. */
    unsigned char status[144]={0};
    if(rt_call(5,fd,(long)status,0,0,0,0)!=0) {rt_call(3,fd,0,0,0,0,0);return -1;}
    unsigned int mode=0;unsigned long size=0;
    for(int i=3;i>=0;--i) mode=(mode<<8)|status[24+i];
    for(int i=7;i>=0;--i) size=(size<<8)|status[48+i];
    if((mode&0170000)!=0100000||size>67108864UL) {
        rt_call(3,fd,0,0,0,0,0);return -1;
    }
    return fd;
}
int rt_read_exact(int fd,void *buffer,unsigned long length) {
    unsigned long used=0;
    for(int calls=0;calls<16384&&used<length;++calls) {
        long n=rt_call(0,fd,(long)((char *)buffer+used),length-used,0,0,0);
        if(n<=0) return 1;
        used+=n;
    }
    return used!=length;
}
long rt_read_file(const char *name,void *buffer,unsigned long capacity) {
    /* No symlink following. Literal proc files are opened by rt_preflight instead. */
    long fd=rt_open_read(name);
    if(fd<0) return -1;
    unsigned long used=0;
    for(int calls=0;calls<16384&&used<capacity;++calls) {
        long n=rt_call(0,fd,(long)((char *)buffer+used),capacity-used,0,0,0);
        if(n<0) {rt_call(3,fd,0,0,0,0,0);return -1;}
        if(n==0) {rt_call(3,fd,0,0,0,0,0);return (long)used;}
        used+=n;
    }
    char extra;
    long n=rt_call(0,fd,(long)&extra,1,0,0,0);
    rt_call(3,fd,0,0,0,0,0);
    return n==0 ? (long)used : -1;
}
int rt_arguments(unsigned long *stack,int expected) {
    if(stack[0]!=(unsigned long)expected||stack[expected+2]!=0) return 1;
    for(int i=1;i<=expected;++i) {
        const char *s=(const char *)stack[i];
        int j=0;
        while(j<256&&s[j]) {if((unsigned char)s[j]<32||(unsigned char)s[j]>=127) return 1;++j;}
        if(j==256) return 1;
    }
    return 0;
}
static const unsigned long *ci_auxv;
int rt_ci_environment(unsigned long *stack) {
    /* Direct CI entry avoids a resident shell/Python launcher. Include the
     * bounded incoming stack environment in startup proof; never print values. */
    if(stack[0]!=5) return 1;
    unsigned long *environment=stack+7,total=0;
    for(int entry=0;entry<256;++entry) {
        char *value=(char *)environment[entry];
        if(!value) {
            ci_auxv=environment+entry+1;
            rt_text("CI_INCOMING_ENV_ENTRIES=");rt_uint((unsigned long)entry);
            rt_text("\nCI_INCOMING_ENV_BYTES=");rt_uint(total);rt_text("\n");return 0;
        }
        unsigned long n=0;while(n<4096&&value[n]) ++n;
        if(n==4096||total+n+1>1048576) return 1;
        for(unsigned long i=0;i<=n;++i) value[i]=0;
        environment[entry]=0;total+=n+1;
    }
    return 1;
}
struct Filter {unsigned short code;unsigned char yes,no;unsigned int k;};
struct Program {unsigned short length;struct Filter *filter;};
int rt_prepare(void) {
    /* Refuse user-space core collectors after setup. Earliest exec entry still
     * requires the selected host's non-piped core_pattern evidence. */
    if(rt_call(157,4,0,0,0,0,0)!=0||rt_call(157,3,0,0,0,0,0)!=0) return 1;
    /* x86-64 kernel sigaction/sigset ABI; no inherited user handler or ignored CHLD. */
    unsigned long action[4]={0,0,0,0},mask=0;
    for(int signal=1;signal<=64;++signal) if(signal!=9&&signal!=19)
        if(rt_call(13,signal,(long)action,0,8,0,0)!=0) return 1;
    return rt_call(14,2,(long)&mask,0,8,0,0)!=0;
}
int rt_policy(int controller) {
    struct Filter f[48]; int n=0;
    f[n++]=(struct Filter){0x20,0,0,4}; /* arch */
    f[n++]=(struct Filter){0x15,1,0,0xc000003e};
    f[n++]=(struct Filter){0x06,0,0,0x80000000};
    f[n++]=(struct Filter){0x20,0,0,0}; /* syscall number */
    const unsigned int base[8]={0,1,3,5,60,79,231,257};
    for(int i=0;i<8;++i) {
        f[n++]=(struct Filter){0x15,0,1,base[i]};
        f[n++]=(struct Filter){0x06,0,0,0x7fff0000};
    }
    if(controller) {
        const unsigned int child[10]={13,14,33,57,61,62,72,157,319,322};
        for(int i=0;i<10;++i) {
            f[n++]=(struct Filter){0x15,0,1,child[i]};
            f[n++]=(struct Filter){0x06,0,0,0x7fff0000};
        }
    }
    f[n++]=(struct Filter){0x06,0,0,0x80000000};
    struct Program p={(unsigned short)n,f};
    if(rt_call(157,38,1,0,0,0,0)!=0) return 1;
    return rt_call(157,22,2,(long)&p,0,0,0)!=0;
}
static char proc_buffer[16384];
static unsigned char self_image[2097152];
int i1_sha256(const unsigned char *,unsigned long,unsigned char *);
static int read_proc(const char *name,char *buffer,unsigned long capacity) {
    long fd=rt_call(257,-100,(long)name,0,0,0,0);
    if(fd<0) return -1;
    long n=rt_call(0,fd,(long)buffer,capacity-1,0,0,0);
    rt_call(3,fd,0,0,0,0,0);
    if(n<=0||n==(long)capacity-1) return -1;
    buffer[n]=0;return (int)n;
}
int rt_preflight(unsigned long bytes,unsigned long *stack) {
    rt_text("I1_PUBLIC_SOFTWARE_ONLY_NOT_ADMITTED\nCOMPONENT_STORAGE_BYTES=");rt_uint(bytes);rt_text("\nMAPS_BEGIN\n");
    if(read_proc("/proc/self/maps",proc_buffer,sizeof(proc_buffer))<0) return 1;
    rt_text(proc_buffer);rt_text("MAPS_END\n");
    if(rt_call(79,(long)proc_buffer,sizeof(proc_buffer),0,0,0,0)<=0) return 1;
    rt_text("CWD=");rt_text(proc_buffer);rt_text("\nARGC=");rt_uint(stack[0]);rt_text("\n");
    for(unsigned long i=1;i<=stack[0];++i) {rt_text("ARG=");rt_text((const char *)stack[i]);rt_text("\n");}
    rt_text("ROLE_ENV_EMPTY=1\n");
    int n=read_proc("/proc/self/status",proc_buffer,sizeof(proc_buffer));
    if(n<0) return 1;
    int single=0;
    for(int i=0;i+10<n;++i) if(proc_buffer[i]=='\n'&&proc_buffer[i+1]=='T'&&
        proc_buffer[i+2]=='h'&&proc_buffer[i+3]=='r'&&proc_buffer[i+4]=='e'&&
        proc_buffer[i+5]=='a'&&proc_buffer[i+6]=='d'&&proc_buffer[i+7]=='s'&&proc_buffer[i+8]==':') {
        int j=i+9;while(j<n&&(proc_buffer[j]==' '||proc_buffer[j]=='\t')) ++j;
        single=j+1<n&&proc_buffer[j]=='1'&&proc_buffer[j+1]=='\n';
    }
    if(!single) return 1;
    rt_text("OBSERVED_THREADS=1\n");
    /* Dumpability zero makes /proc/self/auxv root-owned. Read the actual
     * kernel-provided entry stack instead; preserve its position before CI
     * environment pointers are cleared. No environment values are emitted. */
    const unsigned long *auxv=ci_auxv?ci_auxv:stack+stack[0]+3;
    int terminated=0;rt_text("AUXV_ORIGIN=INITIAL_STACK\nAUXV_SELECTED_BEGIN\n");
    for(int pair=0;pair<64;++pair) {
        unsigned long kind=auxv[2*pair],value=auxv[2*pair+1];
        if(!kind) {terminated=1;break;}
        /* No UID/GID, random bytes or environment value is recorded. */
        if(kind==3||kind==4||kind==5||kind==6||kind==7||kind==8||kind==9||kind==33||kind==51) {
            rt_text("AUX_TYPE=");rt_uint(kind);rt_text(" VALUE=");rt_uint(value);rt_text("\n");
        }
    }
    if(!terminated) return 1;
    rt_text("AUXV_SELECTED_END\nLIMITS_BEGIN\n");
    if(read_proc("/proc/self/limits",proc_buffer,sizeof(proc_buffer))<0) return 1;
    rt_text(proc_buffer);rt_text("LIMITS_END\nCORE_PATTERN=");
    if(read_proc("/proc/sys/kernel/core_pattern",proc_buffer,sizeof(proc_buffer))<0) return 1;
    int piped_core=proc_buffer[0]=='|';
    rt_text(proc_buffer);rt_text("CORE_PATTERN_PIPE_BLOCKS_ADMISSION=");rt_uint(piped_core);
    rt_text("\nDUMPABLE_AFTER_SETUP=0\n");
    long fd=rt_call(257,-100,(long)"/proc/self/exe",0,0,0,0);
    if(fd<0) return 1;
    unsigned long used=0;int complete=0;
    for(int calls=0;calls<16384&&used<sizeof(self_image);++calls) {
        long amount=rt_call(0,fd,(long)(self_image+used),sizeof(self_image)-used,0,0,0);
        if(amount<0) {rt_call(3,fd,0,0,0,0,0);return 1;}
        if(!amount) {complete=1;break;}
        used+=(unsigned long)amount;
    }
    rt_call(3,fd,0,0,0,0,0);
    if(!complete||!used||used>=sizeof(self_image)) return 1;
    unsigned char hash[32];char hex[64];const char *digits="0123456789abcdef";
    if(i1_sha256(self_image,used,hash)) return 1;
    for(int i=0;i<32;++i) {hex[2*i]=digits[hash[i]>>4];hex[2*i+1]=digits[hash[i]&15];}
    rt_text("EXECUTABLE_SHA256=");if(rt_write(1,hex,64)) return 1;rt_text("\n");
    return 0;
}
