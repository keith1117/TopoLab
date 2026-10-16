/* Bind the actual bytes executed; a mutable pathname is not a frozen executable. */
#include "runtime.h"
int i1_sha256(const unsigned char *,unsigned long,unsigned char *);
static unsigned char image[2097152];
int rt_sealed_child(const char *path,const unsigned char *expected) {
    long length=rt_read_file(path,image,sizeof(image));
    if(length<1) return -1;
    unsigned char digest[32];
    if(i1_sha256(image,(unsigned long)length,digest)) return -1;
    for(int i=0;i<32;++i) if(digest[i]!=expected[i]) return -1;
    long fd=rt_call(319,(long)"topolab-i1",19,0,0,0,0); /* CLOEXEC|ALLOW_SEALING|EXEC */
    if(fd<0) return -1;
    if(rt_write(fd,image,(unsigned long)length)||rt_call(72,fd,1033,15,0,0,0)!=0||
       rt_call(72,fd,1034,0,0,0,0)!=15) {rt_call(3,fd,0,0,0,0,0);return -1;}
    return (int)fd;
}
