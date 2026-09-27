/* Deterministic headless mGBA capture runner. Commands come from stdin.
 * Build against mGBA 0.10.5; output captures are real emulator framebuffers.
 * Usage: capture ROM STATE_IN|- STATE_OUT|- . Never modifies the input ROM.
 */
#include <mgba/core/core.h>
#include <mgba/core/interface.h>
#include <mgba/core/log.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void quiet(struct mLogger* l, int c, enum mLogLevel level, const char* f, va_list a) { (void)l;(void)c;(void)level;(void)f;(void)a; }
int main(int argc, char** argv) {
    if(argc!=4) { fprintf(stderr,"usage: capture ROM STATE_IN|- STATE_OUT|-\n");return 2; }
    struct mLogger logger = { .log = quiet };
    mLogSetDefaultLogger(&logger);
    struct mCore* core=mCoreFind(argv[1]);
    if(!core || !core->init(core)) return 2;
    mCoreInitConfig(core,NULL);
    if(!mCoreLoadFile(core,argv[1])) return 2;
    unsigned w,h;core->desiredVideoDimensions(core,&w,&h);
    color_t* pixels=calloc(w*h,sizeof(*pixels));
    core->setVideoBuffer(core,pixels,w);core->reset(core);
    size_t statesize=core->stateSize(core);void* state=malloc(statesize);
    if(strcmp(argv[2],"-")) {
        FILE* f=fopen(argv[2],"rb");
        if(!f || fread(state,1,statesize,f)!=statesize || !core->loadState(core,state)) return 3;
        fclose(f);
    }
    char line[2048],path[1800];unsigned a,b;int frame=0;FILE* video=NULL;
    while(fgets(line,sizeof(line),stdin)) {
        if(sscanf(line,"video %1799s",path)==1) {
            if(video)fclose(video);video=fopen(path,"wb");if(!video)return 4;
        } else if(sscanf(line,"step %u %x",&a,&b)==2) {
            core->setKeys(core,b);
            for(unsigned i=0;i<a;i++) { core->runFrame(core);frame++;if(video)fwrite(pixels,sizeof(*pixels),w*h,video); }
            printf("stepped %u keys %x\n",a,b);
        } else if(sscanf(line,"dump %1799s",path)==1) {
            FILE* f=fopen(path,"wb"); if(!f)return 4;
            fprintf(f,"P6\n%u %u\n255\n",w,h);
            for(unsigned i=0;i<w*h;i++) {
                unsigned char rgb[3]={pixels[i]&255,(pixels[i]>>8)&255,(pixels[i]>>16)&255};
                fwrite(rgb,1,3,f);
            }
            fclose(f);printf("dump %s\n",path);
        } else if(sscanf(line,"read %x %u",&a,&b)==2) {
            printf("memory %08x",a);for(unsigned i=0;i<b;i++)printf(" %02x",core->busRead8(core,a+i));puts("");
        } else if(sscanf(line,"write8 %x %x",&a,&b)==2) {
            core->busWrite8(core,a,b);printf("write8 %08x %02x\n",a,b);
        } else if(sscanf(line,"write16 %x %x",&a,&b)==2) {
            core->busWrite16(core,a,b);printf("write16 %08x %04x\n",a,b);
        } else if(sscanf(line,"record %u %x %1799s",&a,&b,path)==3) {
            FILE* f=fopen(path,"wb");if(!f)return 4;core->setKeys(core,b);
            for(unsigned i=0;i<a;i++) {core->runFrame(core);frame++;fwrite(pixels,sizeof(*pixels),w*h,f);}
            fclose(f);printf("recorded %u RGBA frames to %s\n",a,path);
        } else if(line[0]!='#' && line[0]!='\n') {fprintf(stderr,"bad command: %s",line);return 5;}
        fflush(stdout);
    }
    if(video)fclose(video);
    if(strcmp(argv[3],"-")) {
        if(!core->saveState(core,state))return 3;
        FILE* f=fopen(argv[3],"wb");if(!f)return 3;
        fwrite(state,1,statesize,f);fclose(f);
    }
    free(state);free(pixels);mCoreConfigDeinit(&core->config);core->deinit(core);
    return 0;
}
