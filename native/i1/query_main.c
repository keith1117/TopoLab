/* Public software interface only. No production/pilot command is implemented. */
#include "query.h"
#include "runtime.h"
static unsigned char request[8192],model[131072];
static float parameters[I1_PARAMETERS],prediction[I1_ELEMENTS];
static double raw[I1_ELEMENTS];
static double full_displacement[I1_FULL_DOFS],reactions[I1_FULL_DOFS];
static float nn_input[10*I1_ELEMENTS],nn_label[I1_ELEMENTS];
static int numerical_failure(int code) {
    const I1History *h=i1_history();
    rt_text("I1_PUBLIC_QUERY_FAILURE\ncode=");rt_uint((unsigned long)code);
    rt_text("\nattempted_analyses=");rt_uint((unsigned long)h->analyses);
    rt_text("\nvalid_updated_states=");rt_uint((unsigned long)h->updates);rt_text("\n");
    return 66;
}
static int nearest(const char *path,int n) {
    long fd=rt_open_read(path);if(fd<0) return 1;
    unsigned char magic[8]={0};unsigned int dimensions[2]={0};
    int code=rt_read_exact(fd,magic,8)||rt_read_exact(fd,dimensions,8);
    for(int i=0;i<8;++i) if(magic[i]!=(unsigned char)"I1NN0001"[i]) code=1;
    if(code||dimensions[0]<1||dimensions[0]>528||dimensions[1]!=(unsigned int)n) {
        rt_call(3,fd,0,0,0,0,0);return 1;
    }
    i1_nn_begin();
    for(unsigned int k=0;k<dimensions[0];++k) {
        char id[75];
        if(rt_read_exact(fd,id,sizeof(id))||rt_read_exact(fd,nn_input,10*n*sizeof(float))||
           rt_read_exact(fd,nn_label,n*sizeof(float))||i1_nn_offer(nn_input,nn_label,id)) {
            rt_call(3,fd,0,0,0,0,0);return 1;
        }
    }
    unsigned char extra;
    long trailing=rt_call(0,fd,(long)&extra,1,0,0,0);rt_call(3,fd,0,0,0,0,0);
    return trailing!=0||i1_nn_result(raw);
}
int i1_main(unsigned long *stack) {
    if(stack[0]==2&&!rt_arguments(stack,2)&&rt_equal((const char *)stack[2],"--preflight")) {
        if(rt_prepare()||rt_policy(0)) return 77;
        return rt_preflight(i1_storage_bytes()+sizeof(request)+sizeof(model)+sizeof(parameters)+sizeof(prediction)+sizeof(raw),stack);
    }
    int evaluate=stack[0]==5&&!rt_arguments(stack,5)&&rt_equal((const char *)stack[2],"--public-evaluate");
    if(!evaluate&&(rt_arguments(stack,4)||!rt_equal((const char *)stack[2],"--public-case"))) return 64;
    if(rt_prepare()||rt_policy(0)) return 77;
    long length=rt_read_file((const char *)stack[3],request,sizeof(request));
    if(length<0) return 65;
    I1Case c;int homotopy,limit,initialization;
    if(i1_case_read(request,(unsigned long)length,&c,&homotopy,&limit,&initialization)||i1_setup(&c)) return 65;
    int n=c.nx*c.ny*c.nz;
    union {double value;unsigned long bits;} reference={.value=0};
    if(evaluate&&(rt_read_file((const char *)stack[5],&reference,8)!=8||reference.value<=0||
                   ((reference.bits>>52)&2047)==2047)) return 65;
    int initialization_failure=0;
    if(initialization==1||initialization==4||initialization==5||initialization==6) {
        if(i1_model_role(&c,initialization==5 ? 0 : initialization==6 ? 2 : 1)<0) return 65;
        length=rt_read_file((const char *)stack[4],model,sizeof(model));
        if(length<0||i1_model_read(model,length,parameters)) return 65;
        initialization_failure=i1_predict(parameters,prediction) ? 5 : 0;
        if(!initialization_failure) for(int i=0;i<n;++i) raw[i]=prediction[i];
    } else if(initialization==2) {
        initialization_failure=i1_physics_raw(raw) ? 2 : 0;
    } else if(initialization==3) {
        if(nearest((const char *)stack[4],n)) return 65;
        char matched[75];double distance;
        if(i1_nn_metadata(matched,&distance)) return 65;
        if(rt_write(2,"PUBLIC_NN_MATCH=",16)||rt_write(2,matched,74)||rt_write(2,"\n",1)) return 74;
    } else for(int i=0;i<n;++i) raw[i]=c.volume;
    if(initialization_failure) {
        if(!evaluate) return numerical_failure(initialization_failure);
        /* Preserve a failed candidate rather than treating valid model overflow
         * as malformed input. No incomplete prediction reaches projection. */
        union {unsigned long bits;double value;} invalid={.bits=0x7ff8000000000000UL};
        for(int i=0;i<n;++i) raw[i]=invalid.value;
        if(rt_write(2,initialization_failure==5 ? "PUBLIC_INITIALIZATION_FAILURE=PREDICT\n" :
                    "PUBLIC_INITIALIZATION_FAILURE=PHYSICS\n",sizeof("PUBLIC_INITIALIZATION_FAILURE=PREDICT\n")-1)) return 74;
    }
    int status,succeeded=0,fallback=0;
    if(evaluate) {
        status=i1_evaluate(raw,homotopy ? 1 : initialization==4 ? 2 : 0,limit,
                           reference.value,&succeeded,&fallback);
    } else {
        status=i1_run(raw,homotopy,limit);
        if(status) return numerical_failure(status);
        if(initialization==4&&(status=i1_polish_keep(limit))) return numerical_failure(status);
    }
    const I1History *h=i1_history();
    if(!status&&i1_recover(&c,h->physical[h->selected],h->penalty[h->selected],i1_last_solution(),
                           full_displacement,reactions)) status=6;
    if(evaluate) {
        int metadata[4]={succeeded,fallback,i1_attempt_status(),status};
        if(rt_write(1,"I1EVAL01",8)||rt_write(1,metadata,sizeof(metadata))||
           rt_write(1,i1_attempt_history(),sizeof(*h))) return 74;
        if(status) {
            if(rt_write(1,"I1FAIL01",8)||rt_write(1,h,sizeof(*h))) return 74;
            return 66;
        }
    } else if(status) return numerical_failure(status);
    if(rt_write(1,"I1PUB003",8)||rt_write(1,h,sizeof(*h))||
       rt_write(1,full_displacement,sizeof(full_displacement))||rt_write(1,reactions,sizeof(reactions))) return 74;
    return 0;
}
