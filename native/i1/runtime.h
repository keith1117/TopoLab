/* Linux x86-64 freestanding runtime. Software-only, never a payload grant. */
#ifndef TOPOLAB_I1_RUNTIME_H
#define TOPOLAB_I1_RUNTIME_H
long rt_call(long,long,long,long,long,long,long);
long rt_read_file(const char *,void *,unsigned long);
long rt_open_read(const char *);
int rt_read_exact(int,void *,unsigned long);
int rt_write(int,const void *,unsigned long);
void rt_text(const char *);
void rt_uint(unsigned long);
int rt_equal(const char *,const char *);
int rt_arguments(unsigned long *,int);
int rt_policy(int);
int rt_prepare(void);
int rt_ci_environment(unsigned long *);
int rt_preflight(unsigned long,unsigned long *);
int rt_sealed_child(const char *,const unsigned char *);
#endif
