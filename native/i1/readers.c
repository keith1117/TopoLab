/* Bounded JSON/safetensors readers authored for I1. No directory/index discovery. */
#include "query.h"

#define TOKENS 8192
#define HEADER_LIMIT 8192UL
typedef struct { unsigned long start,end; int next,count; char type; } Token;
static Token tokens[TOKENS];
static int used;
static unsigned long cursor,total;
static const unsigned char *text;

static int equal(int token,const char *s) {
    unsigned long i=0;
    if(token<0||tokens[token].type!='s') return 0;
    while(s[i]) {
        if(tokens[token].start+i>=tokens[token].end||text[tokens[token].start+i]!=(unsigned char)s[i]) return 0;
        ++i;
    }
    return tokens[token].start+i==tokens[token].end;
}
static void space(void) {
    while(cursor<total&&(text[cursor]==' '||text[cursor]=='\n'||text[cursor]=='\r'||text[cursor]=='\t')) ++cursor;
}
/* Entry guard accepts depths0..16; include the rejected depth17 frame in bounds. No VLA. */
static int value(int depth) {
    if(depth>16||used==TOKENS) return -1;
    space(); if(cursor==total) return -1;
    int id=used++;
    tokens[id].start=cursor; tokens[id].count=0;
    unsigned char c=text[cursor++];
    if(c=='{'||c=='[') {
        tokens[id].type=c=='{' ? 'o' : 'a';
        unsigned char end=c=='{' ? '}' : ']';
        space();
        if(cursor<total&&text[cursor]==end) ++cursor;
        else for(int members=0;members<TOKENS;++members) {
            if(c=='{') {
                int key=value(depth+1);
                if(key<0||tokens[key].type!='s') return -1;
                space(); if(cursor==total||text[cursor++]!=':') return -1;
            }
            if(value(depth+1)<0) return -1;
            ++tokens[id].count;
            space(); if(cursor==total) return -1;
            unsigned char next=text[cursor++];
            if(next==end) break;
            if(next!=',') return -1;
            if(members==TOKENS-1) return -1;
        }
    } else if(c=='"') {
        tokens[id].type='s'; tokens[id].start=cursor;
        while(cursor<total&&text[cursor]!='"') {
            if(text[cursor]<32||text[cursor]>=127) return -1;
            if(text[cursor]=='\\') {
                ++cursor;if(cursor==total) return -1;
                unsigned char escape=text[cursor];
                if(escape=='u') {
                    for(int k=0;k<4;++k) {
                        ++cursor;if(cursor==total) return -1;
                        unsigned char digit=text[cursor];
                        if(!((digit>='0'&&digit<='9')||(digit>='a'&&digit<='f')||
                             (digit>='A'&&digit<='F'))) return -1;
                    }
                } else if(escape!='"'&&escape!='\\'&&escape!='/'&&escape!='b'&&
                          escape!='f'&&escape!='n'&&escape!='r'&&escape!='t') return -1;
            }
            ++cursor;
        }
        if(cursor==total) return -1;
        tokens[id].end=cursor++;
    } else {
        tokens[id].type='n';
        if(c=='-') {if(cursor==total) return -1; c=text[cursor++];}
        if(c<'0'||c>'9') return -1;
        if(c=='0'&&cursor<total&&text[cursor]>='0'&&text[cursor]<='9') return -1;
        while(cursor<total&&text[cursor]>='0'&&text[cursor]<='9') ++cursor;
        if(cursor<total&&text[cursor]=='.') {
            ++cursor; unsigned long start=cursor;
            while(cursor<total&&text[cursor]>='0'&&text[cursor]<='9') ++cursor;
            if(cursor==start) return -1;
        }
        if(cursor<total&&(text[cursor]=='e'||text[cursor]=='E')) {
            ++cursor;
            if(cursor<total&&(text[cursor]=='+'||text[cursor]=='-')) ++cursor;
            unsigned long start=cursor;
            while(cursor<total&&text[cursor]>='0'&&text[cursor]<='9') ++cursor;
            if(cursor==start) return -1;
        }
        tokens[id].end=cursor;
        if(cursor-tokens[id].start>32) return -1;
    }
    if(tokens[id].type!='s'&&tokens[id].type!='n') tokens[id].end=cursor;
    tokens[id].next=used;
    return id;
}
static int parse(const unsigned char *bytes,unsigned long length) {
    text=bytes; total=length; cursor=0; used=0;
    if(value(0)!=0) return 1;
    space(); return cursor!=total;
}
static int member(int object,const char *key) {
    if(object<0||tokens[object].type!='o') return -1;
    int found=-1;
    for(int i=object+1;i<tokens[object].next;) {
        int v=i+1;
        if(equal(i,key)) {if(found>=0) return -1;found=v;}
        i=tokens[v].next;
    }
    return found;
}
/* Descriptor counts are lexical nonnegative JSON integers, never rounded reals. */
static int number(int id,double *output) {
    if(id<0||tokens[id].type!='n') return 1;
    unsigned long value=0;
    for(unsigned long i=tokens[id].start;i<tokens[id].end;++i) {
        if(text[i]<'0'||text[i]>'9') return 1;
        value=value*10+(text[i]-'0');
        if(value>2000000UL) return 1;
    }
    *output=(double)value;return 0;
}
/* Physical values are exact IEEE754 bit strings, not an approximate strtod port. */
static int real(int id,double *output) {
    if(id<0||tokens[id].type!='s'||tokens[id].end-tokens[id].start!=16) return 1;
    union {unsigned long long bits;double d;} v={.bits=0};
    for(unsigned long i=tokens[id].start;i<tokens[id].end;++i) {
        unsigned char c=text[i];unsigned int digit;
        if(c>='0'&&c<='9') digit=c-'0';
        else if(c>='a'&&c<='f') digit=c-'a'+10;
        else if(c>='A'&&c<='F') digit=c-'A'+10;
        else return 1;
        v.bits=(v.bits<<4)|digit;
    }
    if((v.bits>>52&2047)==2047) return 1;
    *output=v.d;return 0;
}
static int integer(int id,int *out) {
    double x;
    if(number(id,&x)||x<0||x>2000000||x!=(int)x) return 1;
    *out=(int)x; return 0;
}
static int array_numbers(int id,double *out,int n) {
    if(id<0||tokens[id].type!='a'||tokens[id].count!=n) return 1;
    int t=id+1;
    for(int i=0;i<n;++i) {if(number(t,&out[i])) return 1;t=tokens[t].next;}
    return 0;
}

static int array_reals(int id,double *out,int n) {
    if(id<0||tokens[id].type!='a'||tokens[id].count!=n) return 1;
    int t=id+1;
    for(int i=0;i<n;++i) {if(real(t,&out[i])) return 1;t=tokens[t].next;}
    return 0;
}

int i1_case_read(const unsigned char *bytes,unsigned long length,I1Case *c,
                int *homotopy,int *limit,int *initialization) {
    if(length>8192||parse(bytes,length)||tokens[0].type!='o'||tokens[0].count!=14||
       !equal(member(0,"schema"),"topolab.i1.public-case.v1")) return 1;
    double mesh[3], lengths[3], load[4];
    if(array_numbers(member(0,"mesh"),mesh,3)||array_reals(member(0,"lengths"),lengths,3)||
       array_numbers(member(0,"load"),load,4)) return 1;
    for(int i=0;i<3;++i) if(mesh[i]<1||mesh[i]>24||mesh[i]!=(int)mesh[i]) return 1;
    for(int i=0;i<4;++i) if(load[i]<0||load[i]>24||load[i]!=(int)load[i]) return 1;
    c->nx=mesh[0];c->ny=mesh[1];c->nz=mesh[2];
    c->lx=lengths[0];c->ly=lengths[1];c->lz=lengths[2];
    c->load_x=load[0];c->load_y=load[1];c->load_z=load[2];c->direction=load[3];
    if(real(member(0,"young"),&c->young)||real(member(0,"nu"),&c->nu)||
       real(member(0,"emin"),&c->emin)||real(member(0,"radius"),&c->radius)||
       real(member(0,"volume"),&c->volume)||real(member(0,"minimum"),&c->minimum)||
       real(member(0,"move"),&c->move)||real(member(0,"magnitude"),&c->magnitude)||
       integer(member(0,"limit"),limit)) return 1;
    int method=member(0,"method");
    *homotopy=equal(method,"H")||equal(method,"uniformH");
    *initialization=equal(method,"uniform")||equal(method,"uniformH") ? 0 :
        equal(method,"H")||equal(method,"plainP") ? 1 : equal(method,"C") ? 5 : equal(method,"W") ? 6 :
        equal(method,"physics") ? 2 : equal(method,"NN") ? 3 : equal(method,"Pkeep") ? 4 : -1;
    return *initialization<0||*limit<1||*limit>360;
}

int i1_model_read(const unsigned char *bytes,unsigned long length,float *parameters) {
    if(length<8||length>131072) return 1;
    unsigned long long header=0;
    for(int i=7;i>=0;--i) header=(header<<8)|bytes[i];
    if(header>HEADER_LIMIT||header+8>length||parse(bytes+8,header)||
       tokens[0].type!='o'||(tokens[0].count!=10&&tokens[0].count!=11)) return 1;
    if(tokens[0].count==11) {
        int metadata=member(0,"__metadata__"),topolab=member(metadata,"topolab");
        if(metadata<0||tokens[metadata].type!='o'||tokens[metadata].count!=1||
           topolab<0||tokens[topolab].type!='s'||tokens[topolab].end-tokens[topolab].start>4096) return 1;
        /* Opaque bounded B3 metadata, never decoded/followed as a path or identity grant. */
    }
    const char *names[10]={"network.0.weight","network.0.bias","network.2.weight","network.2.bias",
        "network.4.weight","network.4.bias","network.6.weight","network.6.bias","network.8.weight","network.8.bias"};
    unsigned long begin[10],end[10];
    int offset=0;
    for(int a=0;a<10;++a) {
        int t=member(0,names[a]),count=a==0 ? 5616 : a==8 ? 16 : a%2 ? (a==9 ? 1 : 16) : 6912;
        if(t<0||tokens[t].type!='o'||tokens[t].count!=3||!equal(member(t,"dtype"),"F32")) return 1;
        double shape[5],pair[2];
        int dims=a%2 ? 1 : 5;
        if(array_numbers(member(t,"shape"),shape,dims)||
           array_numbers(member(t,"data_offsets"),pair,2)) return 1;
        if(shape[0]!=(a>=8 ? 1 : 16)) return 1;
        if(!(a%2)&&(shape[1]!=(a==0 ? 13 : 16)||shape[2]!=(a==8 ? 1 : 3)||
           shape[3]!=(a==8 ? 1 : 3)||shape[4]!=(a==8 ? 1 : 3))) return 1;
        if(pair[0]<0||pair[1]<0||pair[0]>105732||pair[1]>105732||
           pair[0]!=(unsigned long)pair[0]||pair[1]!=(unsigned long)pair[1]||
           pair[1]-pair[0]!=4*count) return 1;
        begin[a]=pair[0];end[a]=pair[1];
        if(header+8+end[a]>length) return 1;
        for(int b=0;b<a;++b) if(begin[a]<end[b]&&begin[b]<end[a]) return 1;
        for(int i=0;i<count;++i) {
            unsigned long p=8+header+begin[a]+4*i;
            union { unsigned int u; float f; } v;
            v.u=(unsigned int)bytes[p]|((unsigned int)bytes[p+1]<<8)|
                ((unsigned int)bytes[p+2]<<16)|((unsigned int)bytes[p+3]<<24);
            if((v.u&0x7f800000U)==0x7f800000U) return 1;
            parameters[offset++]=v.f;
        }
    }
    return offset!=I1_PARAMETERS||length!=8+header+105732;
}
