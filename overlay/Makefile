CFLAGS=-DSTANDALONE -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -DTARGET_POSIX -D_LINUX -fPIC -DPIC -D_REENTRANT -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -U_FORTIFY_SOURCE -Wall -g -DHAVE_LIBOPENMAX=2 -DOMX -DOMX_SKIP64BIT -ftree-vectorize -DUSE_EXTERNAL_OMX -DHAVE_LIBBCM_HOST -DUSE_EXTERNAL_LIBBCM_HOST -DUSE_VCHIQ_ARM -Wno-psabi -I/opt/vc/include/ -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux -I/opt/vc/src/hello_pi/libs/ilclient `pkg-config --cflags freetype2` `pkg-config --cflags harfbuzz fontconfig libavformat libavcodec` -I/usr/include/fontconfig -g -Wno-deprecated-declarations -O3
LDFLAGS=-g -Wl,--whole-archive -lilclient -L/opt/vc/lib/ -L/usr/local/lib -lbrcmGLESv2 -lbrcmEGL -lopenmaxil -lbcm_host -lvcos -lvchiq_arm -lpthread -lrt -L/opt/vc/src/hello_pi/libs/ilclient -Wl,--no-whole-archive -rdynamic -lm `pkg-config --libs freetype2` `pkg-config --libs harfbuzz fontconfig libavformat libavcodec`
LDFLAGS+=$(shell libpng-config --ldflags)
DEP_LIBS=/opt/vc/src/hello_pi/libs/ilclient/libilclient.a
SOURCES=pngview.c loadpng.c backgroundLayer.c image.c imageLayer.c log.c text.c key.c
HEADERS=loadpng.h backgroundLayer.h imageLayer.h image.h element_change.h log.h text.h key.h
OBJECTS=$(SOURCES:.c=.o)
EXECUTABLE=overlay
RASPBERRYPI=$(shell sh ./whichpi)
GCCVERSION=$(shell gcc --version | grep ^gcc | sed "s/.* //g")

# detect if we are compiling for RPi 1 or RPi 2 (or 3)
ifeq ($(RASPBERRYPI),Pi1)
	CFLAGS += -mfpu=vfp -mfloat-abi=hard -march=armv6zk -mtune=arm1176jzf-s
else
ifneq (,$(findstring 4.6.,$(GCCVERSION)))  # gcc version 4.6.x
	CFLAGS += -mfpu=neon-vfpv4 -mfloat-abi=hard -march=armv7-a
else  # other gcc versions
	CFLAGS += -mfpu=neon-vfpv4 -mfloat-abi=hard -march=armv7-a -mtune=cortex-a7
endif
endif

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS) $(DEP_LIBS)
	cc $(OBJECTS) -o $@ $(LDFLAGS)

%.o: %.c $(HEADERS)
	cc -c $< -o $@ $(CFLAGS)

.PHONY: clean

clean:
	rm -f $(EXECUTABLE) $(OBJECTS)
